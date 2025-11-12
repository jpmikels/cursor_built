"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from database import engine, Base
from api.v1 import router as api_v1_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info(f"Starting {settings.app_name} in {settings.environment} environment")
    logger.info(f"Project ID: {settings.project_id}")
    
    # Create database tables (in production, use Alembic migrations)
    if settings.environment == "dev":
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Production-grade financial statement consolidation and business valuation platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "prod" else None,
    redoc_url="/redoc" if settings.environment != "prod" else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(api_v1_router, prefix="/api/v1")


# Health check endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "vwb-backend"}


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    # TODO: Add database connectivity check
    return {"status": "ready", "service": "vwb-backend"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.app_name,
        "version": "1.0.0",
        "environment": settings.environment,
        "docs": "/docs" if settings.environment != "prod" else "disabled"
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.environment == "dev" else "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.environment == "dev",
        log_level=settings.log_level.lower()
    )

@app.get("/health")
def health(): return {"ok": True}

@app.get("/ready")
def ready(): return {"ready": True}

