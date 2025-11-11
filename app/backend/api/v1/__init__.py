"""API v1 router."""
from fastapi import APIRouter

from .auth import router as auth_router
from .engagements import router as engagements_router
from .documents import router as documents_router
from .validation import router as validation_router
from .valuation import router as valuation_router

# Create main v1 router
router = APIRouter()

# Include sub-routers
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(engagements_router, prefix="/engagements", tags=["Engagements"])
router.include_router(documents_router, tags=["Documents"])
router.include_router(validation_router, tags=["Validation"])
router.include_router(valuation_router, tags=["Valuation"])

