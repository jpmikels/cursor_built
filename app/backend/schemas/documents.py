"""Document-related schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class UploadUrlRequest(BaseModel):
    """Request for signed upload URL."""
    filename: str
    document_type: str
    mime_type: str


class UploadUrlResponse(BaseModel):
    """Signed upload URL response."""
    upload_url: str
    document_id: int
    gcs_path: str
    expires_in: int = 3600


class DocumentResponse(BaseModel):
    """Document metadata response."""
    id: int
    engagement_id: int
    document_type: str
    original_filename: str
    gcs_path: str
    file_size_bytes: Optional[int]
    mime_type: Optional[str]
    uploaded_by: Optional[int]
    uploaded_at: datetime
    is_parsed: bool
    parsed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class IngestRequest(BaseModel):
    """Start ingestion workflow."""
    document_ids: Optional[list[int]] = None  # If None, ingest all unparsed docs

