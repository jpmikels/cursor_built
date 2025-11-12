"""Database connection and session management (Cloud Run safe)."""
from typing import Generator, Optional
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from config import settings  # keep if you use other settings (e.g., db_echo)

Base = declarative_base()

# ---- configuration / defaults ----
DEFAULT_SQLITE_URL = "sqlite:///./vwb.sqlite3"

def _db_url() -> str:
    # Prefer explicit env var; fall back to settings.database_url if present; then sqlite.
    return (
        os.getenv("DATABASE_URL")
        or getattr(settings, "database_url", None)
        or DEFAULT_SQLITE_URL
    )

def _is_sqlite(url: str) -> bool:
    return url.startswith("sqlite:///")

# Lazily created globals
_engine = None            # type: Optional[any]
_SessionLocal = None      # type: Optional[sessionmaker]

def get_engine():
    """Create engine lazily to avoid import-time failures on Cloud Run."""
    global _engine
    if _engine is not None:
        return _engine

    url = _db_url()
    kwargs = {
        "echo": getattr(settings, "db_echo", False),
        "pool_pre_ping": True,
        # you can optionally add pool_size/max_overflow for non-sqlite
    }

    if _is_sqlite(url):
        # SQLite needs this arg in single-process servers
        kwargs["connect_args"] = {"check_same_thread": False}

    _engine = create_engine(url, **kwargs)
    return _engine

def get_sessionmaker():
    """Return a SessionLocal factory bound to the lazy engine."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=get_engine()
        )
    return _SessionLocal

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session."""
    SessionLocal = get_sessionmaker()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
