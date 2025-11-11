"""Documents and ingestion API endpoints."""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from google.cloud import storage, pubsub_v1
import json

from database import get_db
from models import User, Engagement, Document, Job, JobStatus, DocumentType
from schemas.documents import (
    UploadUrlRequest, UploadUrlResponse, DocumentResponse, IngestRequest
)
from auth.dependencies import get_current_user
from config import settings

router = APIRouter()

# Initialize GCP clients
storage_client = storage.Client(project=settings.project_id)
publisher = pubsub_v1.PublisherClient()


@router.post("/engagements/{engagement_id}/upload", response_model=UploadUrlResponse)
async def get_upload_url(
    engagement_id: int,
    request: UploadUrlRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a signed URL for uploading a document."""
    # Verify engagement exists and user has access
    engagement = db.query(Engagement).filter(
        Engagement.id == engagement_id,
        Engagement.tenant_id == current_user.tenant_id
    ).first()
    
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")
    
    # Validate document type
    try:
        doc_type = DocumentType(request.document_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document type. Must be one of: {[t.value for t in DocumentType]}"
        )
    
    # Generate GCS path
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    gcs_path = f"{current_user.tenant_id}/{engagement_id}/raw/{timestamp}_{request.filename}"
    
    # Create document record
    document = Document(
        engagement_id=engagement_id,
        document_type=doc_type,
        original_filename=request.filename,
        gcs_path=gcs_path,
        mime_type=request.mime_type,
        uploaded_by=current_user.id
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Generate signed URL
    bucket = storage_client.bucket(settings.uploads_bucket)
    blob = bucket.blob(gcs_path)
    
    signed_url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(hours=1),
        method="PUT",
        content_type=request.mime_type
    )
    
    return {
        "upload_url": signed_url,
        "document_id": document.id,
        "gcs_path": gcs_path,
        "expires_in": 3600
    }


@router.get("/engagements/{engagement_id}/documents", response_model=list[DocumentResponse])
async def list_documents(
    engagement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all documents for an engagement."""
    # Verify engagement access
    engagement = db.query(Engagement).filter(
        Engagement.id == engagement_id,
        Engagement.tenant_id == current_user.tenant_id
    ).first()
    
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")
    
    documents = db.query(Document).filter(
        Document.engagement_id == engagement_id
    ).order_by(Document.uploaded_at.desc()).all()
    
    return documents


@router.post("/engagements/{engagement_id}/ingest", status_code=status.HTTP_202_ACCEPTED)
async def start_ingestion(
    engagement_id: int,
    request: IngestRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start document ingestion workflow."""
    # Verify engagement access
    engagement = db.query(Engagement).filter(
        Engagement.id == engagement_id,
        Engagement.tenant_id == current_user.tenant_id
    ).first()
    
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")
    
    # Create ingestion job
    job = Job(
        engagement_id=engagement_id,
        job_type="ingestion",
        status=JobStatus.PENDING,
        message="Ingestion queued"
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Publish to Pub/Sub
    topic_path = f"projects/{settings.project_id}/topics/{settings.pubsub_topic_ingestion}"
    
    message_data = {
        "job_id": job.id,
        "engagement_id": engagement_id,
        "tenant_id": current_user.tenant_id,
        "document_ids": request.document_ids
    }
    
    message_json = json.dumps(message_data).encode("utf-8")
    future = publisher.publish(topic_path, message_json)
    
    try:
        future.result(timeout=5)
    except Exception as e:
        job.status = JobStatus.FAILED
        job.message = f"Failed to queue ingestion: {str(e)}"
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to start ingestion")
    
    return {
        "job_id": job.id,
        "message": "Ingestion started",
        "status": "pending"
    }


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get document details."""
    document = db.query(Document).join(Engagement).filter(
        Document.id == document_id,
        Engagement.tenant_id == current_user.tenant_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a document."""
    document = db.query(Document).join(Engagement).filter(
        Document.id == document_id,
        Engagement.tenant_id == current_user.tenant_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete from GCS
    try:
        bucket = storage_client.bucket(settings.uploads_bucket)
        blob = bucket.blob(document.gcs_path)
        blob.delete()
    except Exception:
        pass  # Continue even if GCS deletion fails
    
    db.delete(document)
    db.commit()

