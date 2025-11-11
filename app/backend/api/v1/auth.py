"""Authentication API endpoints."""
import re
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, Tenant, UserRole
from schemas.auth import LoginRequest, RegisterRequest, Token, UserResponse
from auth.jwt import verify_password, get_password_hash, create_access_token
from auth.dependencies import get_current_user

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user and tenant."""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create tenant slug from name
    tenant_slug = re.sub(r'[^a-z0-9]+', '-', request.tenant_name.lower()).strip('-')
    
    # Check if tenant slug exists
    existing_tenant = db.query(Tenant).filter(Tenant.slug == tenant_slug).first()
    if existing_tenant:
        tenant_slug = f"{tenant_slug}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    # Create tenant
    tenant = Tenant(
        name=request.tenant_name,
        slug=tenant_slug,
        is_active=True
    )
    db.add(tenant)
    db.flush()
    
    # Create user
    user = User(
        tenant_id=tenant.id,
        email=request.email,
        hashed_password=get_password_hash(request.password),
        full_name=request.full_name,
        role=UserRole.ADMIN,  # First user is admin
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "tenant_id": user.tenant_id,
            "role": user.role.value
        }
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "tenant_id": user.tenant_id,
            "role": user.role.value
        }
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user

