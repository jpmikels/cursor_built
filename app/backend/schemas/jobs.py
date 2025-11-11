"""Job-related schemas."""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel


class JobResponse(BaseModel):
    """Job status response."""
    id: int
    engagement_id: int
    job_type: str
    status: str
    progress_percent: int
    message: Optional[str]
    error_details: Optional[dict[str, Any]]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class EngagementStatusResponse(BaseModel):
    """Overall engagement status."""
    engagement_id: int
    current_jobs: list[JobResponse]
    documents_count: int
    parsed_documents: int
    validation_issues: int
    unresolved_issues: int
    valuations_count: int
    latest_valuation: Optional[dict[str, Any]]

