"""Validation-related schemas."""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel


class ValidationIssueResponse(BaseModel):
    """Validation issue response."""
    id: int
    engagement_id: int
    severity: str
    rule_code: Optional[str]
    description: str
    affected_line_items: Optional[list[Any]]
    ai_suggestion: Optional[str]
    ai_confidence: Optional[float]
    is_resolved: bool
    resolution_action: Optional[str]
    resolution_notes: Optional[str]
    resolved_by: Optional[int]
    resolved_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ValidationListResponse(BaseModel):
    """List of validation issues."""
    issues: list[ValidationIssueResponse]
    total: int
    errors: int
    warnings: int
    info: int
    unresolved: int


class AcceptSuggestionRequest(BaseModel):
    """Accept AI suggestion."""
    issue_id: int
    notes: Optional[str] = None


class OverrideSuggestionRequest(BaseModel):
    """Override AI suggestion with manual fix."""
    issue_id: int
    action: str
    notes: str

