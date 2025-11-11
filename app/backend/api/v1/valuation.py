"""Valuation API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2
import json
from datetime import datetime, timedelta

from database import get_db
from models import User, Engagement, ValuationRun, JobStatus
from schemas.valuation import ValuationRunRequest, ValuationRunResponse, ValuationResultDetail
from auth.dependencies import get_current_user
from config import settings

router = APIRouter()

# Initialize Cloud Tasks client
tasks_client = tasks_v2.CloudTasksClient()


@router.post("/engagements/{engagement_id}/valuation/run", response_model=ValuationRunResponse, status_code=status.HTTP_202_ACCEPTED)
async def run_valuation(
    engagement_id: int,
    request: ValuationRunRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute valuation for an engagement."""
    # Verify engagement access
    engagement = db.query(Engagement).filter(
        Engagement.id == engagement_id,
        Engagement.tenant_id == current_user.tenant_id
    ).first()
    
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")
    
    # Get next run number
    max_run = db.query(ValuationRun).filter(
        ValuationRun.engagement_id == engagement_id
    ).order_by(ValuationRun.run_number.desc()).first()
    
    run_number = (max_run.run_number + 1) if max_run else 1
    
    # Create valuation run
    valuation_run = ValuationRun(
        engagement_id=engagement_id,
        run_number=run_number,
        run_name=request.run_name or f"Run {run_number}",
        valuation_date=request.valuation_date,
        methods_config=request.methods.model_dump() if hasattr(request.methods, 'model_dump') else request.methods,
        assumptions={
            "wacc": request.wacc_inputs.model_dump(),
            "method_weights": request.method_weights
        },
        status=JobStatus.PENDING,
        created_by=current_user.id
    )
    db.add(valuation_run)
    db.commit()
    db.refresh(valuation_run)
    
    # Queue valuation task
    parent = tasks_client.queue_path(
        settings.project_id,
        settings.cloud_tasks_location,
        settings.cloud_tasks_queue
    )
    
    task_payload = {
        "valuation_run_id": valuation_run.id,
        "engagement_id": engagement_id,
        "tenant_id": current_user.tenant_id
    }
    
    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": f"{settings.project_id}/valuation/execute",  # Internal endpoint
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(task_payload).encode()
        }
    }
    
    # Schedule task to run immediately
    try:
        response = tasks_client.create_task(request={"parent": parent, "task": task})
    except Exception as e:
        valuation_run.status = JobStatus.FAILED
        valuation_run.results_detail = {"error": str(e)}
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to queue valuation task: {str(e)}")
    
    return valuation_run


@router.get("/engagements/{engagement_id}/valuation/result", response_model=ValuationResultDetail)
async def get_valuation_result(
    engagement_id: int,
    run_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get valuation results."""
    # Verify engagement access
    engagement = db.query(Engagement).filter(
        Engagement.id == engagement_id,
        Engagement.tenant_id == current_user.tenant_id
    ).first()
    
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")
    
    # Get valuation run
    if run_id:
        valuation_run = db.query(ValuationRun).filter(
            ValuationRun.id == run_id,
            ValuationRun.engagement_id == engagement_id
        ).first()
    else:
        # Get latest completed run
        valuation_run = db.query(ValuationRun).filter(
            ValuationRun.engagement_id == engagement_id,
            ValuationRun.status == JobStatus.COMPLETED
        ).order_by(ValuationRun.created_at.desc()).first()
    
    if not valuation_run:
        raise HTTPException(status_code=404, detail="Valuation run not found")
    
    # Extract detailed results
    results_detail = valuation_run.results_detail or {}
    
    return {
        "run": valuation_run,
        "dcf_details": results_detail.get("dcf"),
        "gpcm_details": results_detail.get("gpcm"),
        "gtm_details": results_detail.get("gtm"),
        "reconciliation": results_detail.get("reconciliation", {})
    }


@router.get("/engagements/{engagement_id}/valuation/runs", response_model=list[ValuationRunResponse])
async def list_valuation_runs(
    engagement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all valuation runs for an engagement."""
    # Verify engagement access
    engagement = db.query(Engagement).filter(
        Engagement.id == engagement_id,
        Engagement.tenant_id == current_user.tenant_id
    ).first()
    
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")
    
    runs = db.query(ValuationRun).filter(
        ValuationRun.engagement_id == engagement_id
    ).order_by(ValuationRun.created_at.desc()).all()
    
    return runs


@router.get("/engagements/{engagement_id}/artifacts/workbook.xlsx")
async def download_workbook(
    engagement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get signed URL for downloading consolidated workbook."""
    from google.cloud import storage
    
    # Verify engagement access
    engagement = db.query(Engagement).filter(
        Engagement.id == engagement_id,
        Engagement.tenant_id == current_user.tenant_id
    ).first()
    
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")
    
    # Generate GCS path for workbook
    workbook_path = f"{current_user.tenant_id}/{engagement_id}/workbook/consolidated.xlsx"
    
    # Check if workbook exists
    storage_client = storage.Client(project=settings.project_id)
    bucket = storage_client.bucket(settings.artifacts_bucket)
    blob = bucket.blob(workbook_path)
    
    if not blob.exists():
        raise HTTPException(status_code=404, detail="Workbook not yet generated")
    
    # Generate signed URL
    signed_url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=15),
        method="GET"
    )
    
    return {"download_url": signed_url, "expires_in": 900}


@router.get("/engagements/{engagement_id}/artifacts/summary.pdf")
async def download_summary(
    engagement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get signed URL for downloading valuation summary PDF."""
    from google.cloud import storage
    
    # Verify engagement access
    engagement = db.query(Engagement).filter(
        Engagement.id == engagement_id,
        Engagement.tenant_id == current_user.tenant_id
    ).first()
    
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")
    
    # Generate GCS path for summary
    summary_path = f"{current_user.tenant_id}/{engagement_id}/reports/summary.pdf"
    
    # Check if summary exists
    storage_client = storage.Client(project=settings.project_id)
    bucket = storage_client.bucket(settings.artifacts_bucket)
    blob = bucket.blob(summary_path)
    
    if not blob.exists():
        raise HTTPException(status_code=404, detail="Summary not yet generated")
    
    # Generate signed URL
    signed_url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=15),
        method="GET"
    )
    
    return {"download_url": signed_url, "expires_in": 900}

