# app/backend/main.py
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from database import Base, get_engine  # lazy engine
# If you have versioned APIs, keep this; else remove.
# from api.vi import router as api_v1_router

# ---------- logging ----------
logging.basicConfig(
    level=getattr(logging, getattr(settings, "log_level", "INFO").upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("vwb-backend")

# ---------- lifespan: non-blocking startup/shutdown ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s (env=%s)", getattr(settings, "app_name", "VWB"), getattr(settings, "environment", "unknown"))

    # Only create tables in dev, and never block startup if DB is missing.
    if getattr(settings, "environment", "prod") == "dev":
        try:
            logger.info("Creating database tables (dev only)…")
            Base.metadata.create_all(bind=get_engine())
            logger.info("DB create_all complete.")
        except Exception as e:
            logger.warning("Skipping DB create_all at startup: %s", e)

    yield

    logger.info("Shutting down application")

# ---------- app ----------
app = FastAPI(
    title=getattr(settings, "app_name", "Valuation Workbench"),
    description="Production-grade financial statement consolidation and valuation API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if getattr(settings, "environment", "prod") != "prod" else None,
    redoc_url="/redoc" if getattr(settings, "environment", "prod") != "prod" else None,
)

# ---------- Configurable CORS ----------
import os

# Allow all by default, or restrict dynamically using an env var
frontend_origin = os.getenv("FRONTEND_ORIGIN", "*")

if frontend_origin == "*":
    allowed_origins = ["*"]
else:
    # Support comma-separated list like: "https://frontend.app,https://admin.app"
    allowed_origins = [origin.strip() for origin in frontend_origin.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- routes ----------
@app.get("/health")
def health():
    return {"ok": True}

@app.get("/ready")
def ready():
    return {"ready": True}

@app.get("/")
def root():
    return {"service": "vwb-backend", "status": "running"}

# If you have API routers, include them here
# app.include_router(api_v1_router, prefix="/api/v1")

# Example error handler (optional)
@app.exception_handler(Exception)
async def unhandled_exc(_, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
