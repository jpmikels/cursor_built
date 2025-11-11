"""Engagement-related schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class EngagementCreate(BaseModel):
    """Create new engagement."""
    name: str
    client_name: Optional[str] = None
    description: Optional[str] = None
    fiscal_year_end: Optional[str] = None
    currency: str = "USD"
    industry_code: Optional[str] = None


class EngagementUpdate(BaseModel):
    """Update engagement."""
    name: Optional[str] = None
    client_name: Optional[str] = None
    description: Optional[str] = None
    fiscal_year_end: Optional[str] = None
    currency: Optional[str] = None
    industry_code: Optional[str] = None
    status: Optional[str] = None


class EngagementResponse(BaseModel):
    """Engagement response."""
    id: int
    tenant_id: int
    name: str
    client_name: Optional[str]
    description: Optional[str]
    fiscal_year_end: Optional[str]
    currency: str
    industry_code: Optional[str]
    status: str
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class EngagementListResponse(BaseModel):
    """List of engagements."""
    engagements: list[EngagementResponse]
    total: int
    page: int
    page_size: int

