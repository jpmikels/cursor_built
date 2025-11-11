"""SQLAlchemy database models."""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, 
    Boolean, Enum, JSON, Numeric, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from database import Base


class UserRole(str, PyEnum):
    """User roles for RBAC."""
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class JobStatus(str, PyEnum):
    """Status of background jobs."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ValidationSeverity(str, PyEnum):
    """Severity of validation issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class DocumentType(str, PyEnum):
    """Types of financial documents."""
    INCOME_STATEMENT = "income_statement"
    BALANCE_SHEET = "balance_sheet"
    CASH_FLOW = "cash_flow"
    EQUITY_STATEMENT = "equity_statement"
    OTHER = "other"


# ========================================
# Core Models
# ========================================

class Tenant(Base):
    """Multi-tenant organization."""
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="tenant")
    engagements = relationship("Engagement", back_populates="tenant")


class User(Base):
    """Application users."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(Enum(UserRole), default=UserRole.ANALYST)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")


class Engagement(Base):
    """Valuation engagement/project."""
    __tablename__ = "engagements"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    name = Column(String(255), nullable=False)
    client_name = Column(String(255))
    description = Column(Text)
    fiscal_year_end = Column(String(10))  # e.g., "12-31"
    currency = Column(String(3), default="USD")
    industry_code = Column(String(20))  # SIC/NAICS
    status = Column(String(50), default="draft")
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="engagements")
    documents = relationship("Document", back_populates="engagement", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="engagement", cascade="all, delete-orphan")
    validations = relationship("ValidationIssue", back_populates="engagement", cascade="all, delete-orphan")
    valuations = relationship("ValuationRun", back_populates="engagement", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_engagements_tenant_created', 'tenant_id', 'created_at'),
    )


class Document(Base):
    """Uploaded financial documents."""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    engagement_id = Column(Integer, ForeignKey("engagements.id"), nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)
    original_filename = Column(String(255), nullable=False)
    gcs_path = Column(String(512), nullable=False)
    file_size_bytes = Column(Integer)
    mime_type = Column(String(100))
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Parsing metadata
    is_parsed = Column(Boolean, default=False)
    parsed_at = Column(DateTime)
    extraction_metadata = Column(JSON)  # Document AI output metadata
    
    # Relationships
    engagement = relationship("Engagement", back_populates="documents")
    
    __table_args__ = (
        Index('ix_documents_engagement', 'engagement_id'),
    )


class Job(Base):
    """Background processing jobs."""
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    engagement_id = Column(Integer, ForeignKey("engagements.id"), nullable=False)
    job_type = Column(String(50), nullable=False)  # ingestion, normalization, validation, valuation
    status = Column(Enum(JobStatus), default=JobStatus.PENDING)
    progress_percent = Column(Integer, default=0)
    message = Column(Text)
    error_details = Column(JSON)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    engagement = relationship("Engagement", back_populates="jobs")
    
    __table_args__ = (
        Index('ix_jobs_engagement_status', 'engagement_id', 'status'),
    )


# ========================================
# Validation Models
# ========================================

class ValidationIssue(Base):
    """Validation issues and AI suggestions."""
    __tablename__ = "validation_issues"
    
    id = Column(Integer, primary_key=True, index=True)
    engagement_id = Column(Integer, ForeignKey("engagements.id"), nullable=False)
    severity = Column(Enum(ValidationSeverity), nullable=False)
    rule_code = Column(String(50))  # e.g., BS_IMBALANCE, NEGATIVE_INVENTORY
    description = Column(Text, nullable=False)
    affected_line_items = Column(JSON)  # List of COA line items
    
    # AI suggestion
    ai_suggestion = Column(Text)
    ai_confidence = Column(Numeric(3, 2))  # 0.00 to 1.00
    
    # Resolution
    is_resolved = Column(Boolean, default=False)
    resolution_action = Column(String(50))  # accepted, overridden, ignored
    resolution_notes = Column(Text)
    resolved_by = Column(Integer, ForeignKey("users.id"))
    resolved_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    engagement = relationship("Engagement", back_populates="validations")
    
    __table_args__ = (
        Index('ix_validations_engagement_resolved', 'engagement_id', 'is_resolved'),
    )


# ========================================
# Valuation Models
# ========================================

class ValuationRun(Base):
    """Valuation execution and results."""
    __tablename__ = "valuation_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    engagement_id = Column(Integer, ForeignKey("engagements.id"), nullable=False)
    run_number = Column(Integer, default=1)
    run_name = Column(String(255))
    
    # Inputs
    valuation_date = Column(DateTime, nullable=False)
    methods_config = Column(JSON)  # Which methods to run + weights
    assumptions = Column(JSON)  # WACC inputs, growth rates, etc.
    
    # Outputs
    dcf_value = Column(Numeric(20, 2))
    gpcm_value = Column(Numeric(20, 2))
    gtm_value = Column(Numeric(20, 2))
    concluded_value = Column(Numeric(20, 2))
    
    # Metadata
    status = Column(Enum(JobStatus), default=JobStatus.PENDING)
    results_detail = Column(JSON)  # Full valuation output
    bq_table_path = Column(String(255))  # Path to detailed results in BigQuery
    
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    engagement = relationship("Engagement", back_populates="valuations")
    
    __table_args__ = (
        Index('ix_valuations_engagement', 'engagement_id'),
        UniqueConstraint('engagement_id', 'run_number', name='uq_engagement_run_number'),
    )


class MarketDataProvider(Base):
    """Configuration for market data providers."""
    __tablename__ = "market_data_providers"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    provider_name = Column(String(100), nullable=False)  # pitchbook, capiq, dealstats, etc.
    is_active = Column(Boolean, default=True)
    credentials_secret_name = Column(String(255))  # Secret Manager secret name
    config = Column(JSON)  # Provider-specific configuration
    last_sync = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'provider_name', name='uq_tenant_provider'),
    )


# ========================================
# Audit Trail
# ========================================

class AuditLog(Base):
    """Audit trail for all significant actions."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    engagement_id = Column(Integer, ForeignKey("engagements.id"))
    
    action = Column(String(100), nullable=False)  # document_uploaded, validation_accepted, etc.
    entity_type = Column(String(50))  # document, validation, valuation, etc.
    entity_id = Column(Integer)
    
    details = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(String(512))
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('ix_audit_tenant_created', 'tenant_id', 'created_at'),
        Index('ix_audit_engagement_created', 'engagement_id', 'created_at'),
    )

