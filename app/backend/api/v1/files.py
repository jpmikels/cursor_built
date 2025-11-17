"""API endpoints for file upload and processing."""
import logging
import uuid
import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from google.cloud import storage, pubsub_v1
from pydantic import BaseModel

from database import get_db
from config import settings
from ai.document_intelligence import document_ai_service

logger = logging.getLogger(__name__)
router = APIRouter()


class SignedUrlRequest(BaseModel):
    """Request for signed upload URLs."""
    files: List[dict]  # [{"name": "file.pdf", "type": "application/pdf"}]


class SignedUrlResponse(BaseModel):
    """Response with signed URLs."""
    urls: List[dict]  # [{"file_id": "...", "signed_url": "...", "name": "..."}]


class FileProcessRequest(BaseModel):
    """Request to process uploaded files."""
    file_ids: List[str]


@router.post("/{engagement_id}/files/upload-url", response_model=SignedUrlResponse)
async def get_upload_urls(
    engagement_id: str,
    request: SignedUrlRequest,
    db: Session = Depends(get_db)
):
    """
    Generate signed URLs for direct upload to Cloud Storage.
    
    This enables client-side uploads without routing through the API server.
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(settings.uploads_bucket)
        
        urls = []
        for file_info in request.files:
            # Generate unique file ID
            file_id = str(uuid.uuid4())
            
            # Create blob path: engagements/{engagement_id}/uploads/{file_id}/{filename}
            blob_name = f"engagements/{engagement_id}/uploads/{file_id}/{file_info['name']}"
            blob = bucket.blob(blob_name)
            
            # Generate signed URL (valid for 1 hour)
            signed_url = blob.generate_signed_url(
                version="v4",
                expiration=3600,
                method="PUT",
                content_type=file_info.get("type", "application/octet-stream")
            )
            
            urls.append({
                "file_id": file_id,
                "signed_url": signed_url,
                "name": file_info["name"],
                "blob_name": blob_name
            })
            
            logger.info(f"Generated signed URL for: {file_info['name']}")
        
        return SignedUrlResponse(urls=urls)
        
    except Exception as e:
        logger.error(f"Error generating signed URLs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{engagement_id}/files")
async def process_files(
    engagement_id: str,
    request: FileProcessRequest,
    db: Session = Depends(get_db)
):
    """
    Trigger processing of uploaded files.
    
    This kicks off:
    1. Document AI extraction
    2. Data parsing and normalization
    3. AI-powered mapping to canonical COA
    """
    try:
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(settings.project_id, settings.pubsub_topic_ingestion)
        
        # Publish message to trigger async processing
        message_data = {
            "engagement_id": engagement_id,
            "file_ids": request.file_ids,
            "action": "process_documents"
        }
        
        future = publisher.publish(
            topic_path,
            json.dumps(message_data).encode("utf-8")
        )
        
        message_id = future.result()
        logger.info(f"Published processing job: {message_id}")
        
        return {
            "status": "processing",
            "job_id": message_id,
            "message": "Files are being processed. Check back shortly."
        }
        
    except Exception as e:
        logger.error(f"Error triggering file processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{engagement_id}/files/{file_id}")
async def get_file_status(
    engagement_id: str,
    file_id: str,
    db: Session = Depends(get_db)
):
    """Get processing status of a file."""
    try:
        # Query database for file processing status
        # This would query your files table
        
        return {
            "file_id": file_id,
            "status": "completed",  # or "processing", "failed"
            "extracted_data": {
                "tables": [],
                "entities": [],
                "text": ""
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching file status: {e}")
        raise HTTPException(status_code=404, detail="File not found")


@router.get("/{engagement_id}/files")
async def list_files(
    engagement_id: str,
    db: Session = Depends(get_db)
):
    """List all files for an engagement."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(settings.uploads_bucket)
        
        # List blobs with prefix
        prefix = f"engagements/{engagement_id}/uploads/"
        blobs = bucket.list_blobs(prefix=prefix)
        
        files = []
        for blob in blobs:
            files.append({
                "name": blob.name.split("/")[-1],
                "size": blob.size,
                "uploaded_at": blob.time_created.isoformat(),
                "content_type": blob.content_type
            })
        
        return {"files": files}
        
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{engagement_id}/files/{file_id}")
async def delete_file(
    engagement_id: str,
    file_id: str,
    db: Session = Depends(get_db)
):
    """Delete a file."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(settings.uploads_bucket)
        
        # Delete all blobs with this file_id
        prefix = f"engagements/{engagement_id}/uploads/{file_id}/"
        blobs = bucket.list_blobs(prefix=prefix)
        
        count = 0
        for blob in blobs:
            blob.delete()
            count += 1
        
        logger.info(f"Deleted {count} files for file_id: {file_id}")
        
        return {"status": "deleted", "files_deleted": count}
        
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        raise HTTPException(status_code=500, detail=str(e))
