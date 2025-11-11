"""Engagements API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models import User, Engagement, Document, Job, ValidationIssue, ValuationRun
from schemas.engagements import (
    EngagementCreate, EngagementUpdate, EngagementResponse, EngagementListResponse
)
from schemas.jobs import EngagementStatusResponse, JobResponse
from auth.dependencies import get_current_user

router = APIRouter()


@router.post("", response_model=EngagementResponse, status_code=status.HTTP_201_CREATED)
async def create_engagement(
    engagement: EngagementCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new engagement."""
    db_engagement = Engagement(
        tenant_id=current_user.tenant_id,
        name=engagement.name,
        client_name=engagement.client_name,
        description=engagement.description,
        fiscal_year_end=engagement.fiscal_year_end,
        currency=engagement.currency,
        industry_code=engagement.industry_code,
        status="draft",
        created_by=current_user.id
    )
    db.add(db_engagement)
    db.commit()
    db.refresh(db_engagement)
    return db_engagement


@router.get("", response_model=EngagementListResponse)
async def list_engagements(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all engagements for the current tenant."""
    query = db.query(Engagement).filter(Engagement.tenant_id == current_user.tenant_id)
    
    total = query.count()
    engagements = query.order_by(Engagement.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "engagements": engagements,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{engagement_id}", response_model=EngagementResponse)
async def get_engagement(
    engagement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get engagement by ID."""
    engagement = db.query(Engagement).filter(
        Engagement.id == engagement_id,
        Engagement.tenant_id == current_user.tenant_id
    ).first()
    
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")
    
    return engagement


@router.patch("/{engagement_id}", response_model=EngagementResponse)
async def update_engagement(
    engagement_id: int,
    engagement_update: EngagementUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update engagement."""
    engagement = db.query(Engagement).filter(
        Engagement.id == engagement_id,
        Engagement.tenant_id == current_user.tenant_id
    ).first()
    
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")
    
    # Update fields
    update_data = engagement_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(engagement, field, value)
    
    db.commit()
    db.refresh(engagement)
    return engagement


@router.delete("/{engagement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_engagement(
    engagement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete engagement."""
    engagement = db.query(Engagement).filter(
        Engagement.id == engagement_id,
        Engagement.tenant_id == current_user.tenant_id
    ).first()
    
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")
    
    db.delete(engagement)
    db.commit()


@router.get("/{engagement_id}/status", response_model=EngagementStatusResponse)
async def get_engagement_status(
    engagement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive engagement status."""
    engagement = db.query(Engagement).filter(
        Engagement.id == engagement_id,
        Engagement.tenant_id == current_user.tenant_id
    ).first()
    
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")
    
    # Get current jobs
    current_jobs = db.query(Job).filter(
        Job.engagement_id == engagement_id,
        Job.status.in_(["pending", "running"])
    ).all()
    
    # Get document counts
    documents_count = db.query(func.count(Document.id)).filter(
        Document.engagement_id == engagement_id
    ).scalar()
    
    parsed_documents = db.query(func.count(Document.id)).filter(
        Document.engagement_id == engagement_id,
        Document.is_parsed == True
    ).scalar()
    
    # Get validation issue counts
    validation_issues = db.query(func.count(ValidationIssue.id)).filter(
        ValidationIssue.engagement_id == engagement_id
    ).scalar()
    
    unresolved_issues = db.query(func.count(ValidationIssue.id)).filter(
        ValidationIssue.engagement_id == engagement_id,
        ValidationIssue.is_resolved == False
    ).scalar()
    
    # Get valuations count
    valuations_count = db.query(func.count(ValuationRun.id)).filter(
        ValuationRun.engagement_id == engagement_id
    ).scalar()
    
    # Get latest valuation
    latest_valuation = db.query(ValuationRun).filter(
        ValuationRun.engagement_id == engagement_id
    ).order_by(ValuationRun.created_at.desc()).first()
    
    return {
        "engagement_id": engagement_id,
        "current_jobs": [JobResponse.model_validate(job) for job in current_jobs],
        "documents_count": documents_count,
        "parsed_documents": parsed_documents,
        "validation_issues": validation_issues,
        "unresolved_issues": unresolved_issues,
        "valuations_count": valuations_count,
        "latest_valuation": {
            "id": latest_valuation.id,
            "run_number": latest_valuation.run_number,
            "concluded_value": float(latest_valuation.concluded_value) if latest_valuation.concluded_value else None,
            "status": latest_valuation.status.value,
            "created_at": latest_valuation.created_at.isoformat()
        } if latest_valuation else None
    }

