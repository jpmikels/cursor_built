"""Authentication schemas."""
from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data."""
    sub: int
    email: str
    tenant_id: int
    role: str


class LoginRequest(BaseModel):
    """Login credentials."""
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str
    full_name: str
    tenant_name: str  # For new tenant creation


class UserResponse(BaseModel):
    """User information response."""
    id: int
    email: str
    full_name: str | None
    role: str
    tenant_id: int
    is_active: bool
    
    class Config:
        from_attributes = True

