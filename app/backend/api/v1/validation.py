"""Validation API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from database import get_db
from models import User, Engagement, ValidationIssue, ValidationSeverity
from schemas.validation import (
    ValidationListResponse, ValidationIssueResponse,
    AcceptSuggestionRequest, OverrideSuggestionRequest
)
from auth.dependencies import get_current_user

router = APIRouter()


@router.get("/engagements/{engagement_id}/validation", response_model=ValidationListResponse)
async def list_validation_issues(
    engagement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all validation issues for an engagement."""
    # Verify engagement access
    engagement = db.query(Engagement).filter(
        Engagement.id == engagement_id,
        Engagement.tenant_id == current_user.tenant_id
    ).first()
    
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")
    
    # Get all issues
    issues = db.query(ValidationIssue).filter(
        ValidationIssue.engagement_id == engagement_id
    ).order_by(
        ValidationIssue.severity,
        ValidationIssue.created_at.desc()
    ).all()
    
    # Count by severity
    severity_counts = db.query(
        ValidationIssue.severity,
        func.count(ValidationIssue.id)
    ).filter(
        ValidationIssue.engagement_id == engagement_id
    ).group_by(ValidationIssue.severity).all()
    
    counts = {severity: count for severity, count in severity_counts}
    
    # Count unresolved
    unresolved = db.query(func.count(ValidationIssue.id)).filter(
        ValidationIssue.engagement_id == engagement_id,
        ValidationIssue.is_resolved == False
    ).scalar()
    
    return {
        "issues": issues,
        "total": len(issues),
        "errors": counts.get(ValidationSeverity.ERROR, 0),
        "warnings": counts.get(ValidationSeverity.WARNING, 0),
        "info": counts.get(ValidationSeverity.INFO, 0),
        "unresolved": unresolved
    }


@router.post("/engagements/{engagement_id}/validation/accept")
async def accept_suggestion(
    engagement_id: int,
    request: AcceptSuggestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accept an AI suggestion."""
    # Verify engagement access
    engagement = db.query(Engagement).filter(
        Engagement.id == engagement_id,
        Engagement.tenant_id == current_user.tenant_id
    ).first()
    
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")
    
    # Get validation issue
    issue = db.query(ValidationIssue).filter(
        ValidationIssue.id == request.issue_id,
        ValidationIssue.engagement_id == engagement_id
    ).first()
    
    if not issue:
        raise HTTPException(status_code=404, detail="Validation issue not found")
    
    if issue.is_resolved:
        raise HTTPException(status_code=400, detail="Issue already resolved")
    
    # Mark as resolved
    issue.is_resolved = True
    issue.resolution_action = "accepted"
    issue.resolution_notes = request.notes
    issue.resolved_by = current_user.id
    issue.resolved_at = datetime.utcnow()
    
    db.commit()
    
    # TODO: Trigger re-normalization/recalculation based on accepted suggestion
    
    return {"message": "Suggestion accepted", "issue_id": issue.id}


@router.post("/engagements/{engagement_id}/validation/override")
async def override_suggestion(
    engagement_id: int,
    request: OverrideSuggestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Override AI suggestion with manual fix."""
    # Verify engagement access
    engagement = db.query(Engagement).filter(
        Engagement.id == engagement_id,
        Engagement.tenant_id == current_user.tenant_id
    ).first()
    
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")
    
    # Get validation issue
    issue = db.query(ValidationIssue).filter(
        ValidationIssue.id == request.issue_id,
        ValidationIssue.engagement_id == engagement_id
    ).first()
    
    if not issue:
        raise HTTPException(status_code=404, detail="Validation issue not found")
    
    if issue.is_resolved:
        raise HTTPException(status_code=400, detail="Issue already resolved")
    
    # Mark as resolved with override
    issue.is_resolved = True
    issue.resolution_action = "overridden"
    issue.resolution_notes = f"Action: {request.action}. Notes: {request.notes}"
    issue.resolved_by = current_user.id
    issue.resolved_at = datetime.utcnow()
    
    db.commit()
    
    # TODO: Apply manual override action
    
    return {"message": "Suggestion overridden", "issue_id": issue.id}


@router.get("/validation/{issue_id}", response_model=ValidationIssueResponse)
async def get_validation_issue(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get validation issue details."""
    issue = db.query(ValidationIssue).join(Engagement).filter(
        ValidationIssue.id == issue_id,
        Engagement.tenant_id == current_user.tenant_id
    ).first()
    
    if not issue:
        raise HTTPException(status_code=404, detail="Validation issue not found")
    
    return issue

