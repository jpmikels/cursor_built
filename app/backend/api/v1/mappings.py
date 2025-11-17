"""API endpoints for COA mapping and normalization."""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from config import settings
from ai.gemini_service import gemini_service

logger = logging.getLogger(__name__)
router = APIRouter()


class SourceLineItem(BaseModel):
    """Source financial statement line item."""
    id: str
    name: str
    value: float
    period: str
    statement_type: str  # "income_statement", "balance_sheet", "cash_flow"


class MappingRequest(BaseModel):
    """Request for AI-powered mapping."""
    source_items: List[SourceLineItem]
    industry: str
    target_coa: Optional[str] = "default"  # COA template to use


class Mapping(BaseModel):
    """Mapping from source to canonical COA."""
    source_id: str
    source_name: str
    target_id: str
    target_name: str
    confidence: float
    reasoning: str
    status: str = "pending"  # "pending", "approved", "rejected"


class MappingResponse(BaseModel):
    """Response with AI-generated mappings."""
    mappings: List[Mapping]
    summary: dict


class ApprovalRequest(BaseModel):
    """Request to approve/reject mappings."""
    mapping_ids: List[str]
    action: str  # "approve" or "reject"
    overrides: Optional[dict] = None


@router.post("/{engagement_id}/mappings/suggest", response_model=MappingResponse)
async def suggest_mappings(
    engagement_id: str,
    request: MappingRequest,
    db: Session = Depends(get_db)
):
    """
    Generate AI-powered mapping suggestions.
    
    Uses Gemini to intelligently map source line items to canonical COA.
    """
    try:
        # Load canonical COA
        canonical_coa = _load_canonical_coa(request.target_coa)
        
        # Prepare source items for Gemini
        source_items_dict = [
            {
                "id": item.id,
                "name": item.name,
                "value": item.value,
                "type": item.statement_type
            }
            for item in request.source_items
        ]
        
        # Call Gemini for intelligent mapping
        logger.info(f"Requesting AI mapping for {len(source_items_dict)} items")
        ai_mappings = await gemini_service.map_to_coa(
            source_items=source_items_dict,
            industry=request.industry,
            canonical_coa=canonical_coa
        )
        
        # Convert to response format
        mappings = [
            Mapping(
                source_id=m["source_id"],
                source_name=m["source_name"],
                target_id=m["target_id"],
                target_name=m["target_name"],
                confidence=m["confidence"],
                reasoning=m["reasoning"],
                status="approved" if m["confidence"] > 0.9 else "pending"
            )
            for m in ai_mappings
        ]
        
        # Calculate summary stats
        summary = {
            "total_items": len(mappings),
            "high_confidence": len([m for m in mappings if m.confidence > 0.9]),
            "medium_confidence": len([m for m in mappings if 0.7 <= m.confidence <= 0.9]),
            "low_confidence": len([m for m in mappings if m.confidence < 0.7]),
            "auto_approved": len([m for m in mappings if m.status == "approved"])
        }
        
        logger.info(f"Generated {len(mappings)} mappings: {summary}")
        
        # TODO: Save mappings to database
        
        return MappingResponse(mappings=mappings, summary=summary)
        
    except Exception as e:
        logger.error(f"Error generating mappings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{engagement_id}/mappings/approve")
async def approve_mappings(
    engagement_id: str,
    request: ApprovalRequest,
    db: Session = Depends(get_db)
):
    """
    Approve or reject AI-suggested mappings.
    
    Allows manual review and override of AI suggestions.
    """
    try:
        # TODO: Update mappings in database
        # - Set status to "approved" or "rejected"
        # - Apply any manual overrides
        # - Trigger next stage (validation)
        
        logger.info(f"{request.action} {len(request.mapping_ids)} mappings")
        
        return {
            "status": "success",
            "action": request.action,
            "updated_count": len(request.mapping_ids)
        }
        
    except Exception as e:
        logger.error(f"Error approving mappings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{engagement_id}/mappings")
async def get_mappings(
    engagement_id: str,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all mappings for an engagement."""
    try:
        # TODO: Query mappings from database
        # Filter by status if provided
        
        return {
            "mappings": [],
            "summary": {
                "total": 0,
                "pending": 0,
                "approved": 0,
                "rejected": 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching mappings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{engagement_id}/mappings/{mapping_id}")
async def update_mapping(
    engagement_id: str,
    mapping_id: str,
    mapping: Mapping,
    db: Session = Depends(get_db)
):
    """Update a specific mapping (manual override)."""
    try:
        # TODO: Update mapping in database
        
        logger.info(f"Updated mapping {mapping_id}: {mapping.source_name} -> {mapping.target_name}")
        
        return {"status": "updated", "mapping": mapping}
        
    except Exception as e:
        logger.error(f"Error updating mapping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _load_canonical_coa(template: str = "default") -> List[dict]:
    """Load canonical chart of accounts template."""
    # TODO: Load from database or config file
    # For now, return a sample structure
    
    return [
        {
            "id": "revenue",
            "name": "Revenue",
            "parent": None,
            "type": "income_statement",
            "children": [
                {"id": "revenue.product", "name": "Product Revenue"},
                {"id": "revenue.service", "name": "Service Revenue"},
                {"id": "revenue.other", "name": "Other Revenue"}
            ]
        },
        {
            "id": "cogs",
            "name": "Cost of Revenue",
            "parent": None,
            "type": "income_statement",
            "children": [
                {"id": "cogs.materials", "name": "Direct Materials"},
                {"id": "cogs.labor", "name": "Direct Labor"},
                {"id": "cogs.overhead", "name": "Manufacturing Overhead"}
            ]
        },
        {
            "id": "opex",
            "name": "Operating Expenses",
            "parent": None,
            "type": "income_statement",
            "children": [
                {"id": "opex.rd", "name": "Research & Development"},
                {"id": "opex.sales", "name": "Sales & Marketing"},
                {"id": "opex.ga", "name": "General & Administrative"}
            ]
        }
    ]
