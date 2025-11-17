"""API endpoints for valuation workbook generation."""
import logging
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from io import BytesIO
from google.cloud import storage

from database import get_db
from config import settings
from workbook.generator import ValuationWorkbookGenerator

logger = logging.getLogger(__name__)
router = APIRouter()


class WorkbookRequest(BaseModel):
    """Request to generate valuation workbook."""
    include_tabs: Optional[list] = None  # Specific tabs to include
    format: str = "xlsx"  # "xlsx" or "google_sheets"
    template: str = "standard"  # "standard", "simplified", "detailed"


class WorkbookResponse(BaseModel):
    """Response with workbook info."""
    workbook_id: str
    download_url: str
    google_sheets_url: Optional[str] = None
    status: str


@router.post("/{engagement_id}/workbook/generate", response_model=WorkbookResponse)
async def generate_workbook(
    engagement_id: str,
    request: WorkbookRequest,
    db: Session = Depends(get_db)
):
    """
    Generate comprehensive valuation workbook with formulas.
    
    Creates a multi-tab Excel workbook with:
    - Normalized financial statements
    - Forecasts with assumptions
    - DCF valuation
    - Comparable company analysis
    - Sensitivity tables
    - Charts and visualizations
    """
    try:
        # Get engagement data
        engagement_data = await _get_engagement_data(engagement_id, db)
        
        # Generate workbook
        logger.info(f"Generating {request.format} workbook for engagement {engagement_id}")
        
        generator = ValuationWorkbookGenerator(engagement_data)
        workbook_bytes = generator.generate()
        
        # Upload to Cloud Storage
        storage_client = storage.Client()
        bucket = storage_client.bucket(settings.artifacts_bucket)
        
        workbook_id = str(uuid.uuid4())
        blob_name = f"engagements/{engagement_id}/workbooks/{workbook_id}.xlsx"
        blob = bucket.blob(blob_name)
        
        blob.upload_from_string(
            workbook_bytes,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # Generate signed download URL (valid for 1 hour)
        download_url = blob.generate_signed_url(
            version="v4",
            expiration=3600,
            method="GET"
        )
        
        logger.info(f"Workbook generated successfully: {workbook_id}")
        
        # TODO: Save workbook record to database
        
        return WorkbookResponse(
            workbook_id=workbook_id,
            download_url=download_url,
            status="completed"
        )
        
    except Exception as e:
        logger.error(f"Error generating workbook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{engagement_id}/workbook/{workbook_id}/download")
async def download_workbook(
    engagement_id: str,
    workbook_id: str,
    db: Session = Depends(get_db)
):
    """Download a previously generated workbook."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(settings.artifacts_bucket)
        
        blob_name = f"engagements/{engagement_id}/workbooks/{workbook_id}.xlsx"
        blob = bucket.blob(blob_name)
        
        if not blob.exists():
            raise HTTPException(status_code=404, detail="Workbook not found")
        
        # Stream file
        workbook_bytes = blob.download_as_bytes()
        
        return StreamingResponse(
            BytesIO(workbook_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=valuation_{engagement_id}.xlsx"
            }
        )
        
    except Exception as e:
        logger.error(f"Error downloading workbook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{engagement_id}/workbook")
async def list_workbooks(
    engagement_id: str,
    db: Session = Depends(get_db)
):
    """List all workbooks generated for an engagement."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(settings.artifacts_bucket)
        
        prefix = f"engagements/{engagement_id}/workbooks/"
        blobs = bucket.list_blobs(prefix=prefix)
        
        workbooks = []
        for blob in blobs:
            workbook_id = blob.name.split("/")[-1].replace(".xlsx", "")
            workbooks.append({
                "workbook_id": workbook_id,
                "created_at": blob.time_created.isoformat(),
                "size_bytes": blob.size,
                "download_url": blob.generate_signed_url(
                    version="v4",
                    expiration=3600,
                    method="GET"
                )
            })
        
        return {"workbooks": workbooks, "total": len(workbooks)}
        
    except Exception as e:
        logger.error(f"Error listing workbooks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{engagement_id}/workbook/{workbook_id}/export-google-sheets")
async def export_to_google_sheets(
    engagement_id: str,
    workbook_id: str,
    db: Session = Depends(get_db)
):
    """Export workbook to Google Sheets."""
    try:
        # TODO: Implement Google Sheets API integration
        # 1. Download workbook from GCS
        # 2. Convert to Google Sheets format
        # 3. Share with user
        
        return {
            "status": "exported",
            "google_sheets_url": "https://docs.google.com/spreadsheets/d/..."
        }
        
    except Exception as e:
        logger.error(f"Error exporting to Google Sheets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions

async def _get_engagement_data(engagement_id: str, db: Session) -> dict:
    """Get all engagement data for workbook generation."""
    # TODO: Query from database
    # Include: company info, financials, mappings, assumptions, valuation results
    
    return {
        "engagement_id": engagement_id,
        "company_name": "Example Corp",
        "industry": "SaaS",
        "valuation_date": "2024-01-01",
        "historical_years": [2021, 2022, 2023],
        "forecast_years": 5,
        "revenue": [1000000, 1500000, 2000000],
        "cogs": [300000, 450000, 600000],
        "operating_expenses": [500000, 700000, 900000],
        "assumptions": {
            "revenue_growth": [0.15, 0.12, 0.10, 0.08, 0.06],
            "gross_margin": 0.70,
            "tax_rate": 0.21,
            "wacc": 0.12,
            "terminal_growth": 0.03
        },
        "valuation_results": {
            "enterprise_value": 50000000,
            "equity_value": 48000000,
            "per_share_value": 48.00
        }
    }
