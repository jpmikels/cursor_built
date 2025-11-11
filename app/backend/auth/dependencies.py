"""Authentication dependencies for FastAPI."""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole
from auth.jwt import decode_access_token

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user from JWT token."""
    token = credentials.credentials
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: Optional[int] = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure the user is active."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


class RoleChecker:
    """Dependency to check user role."""
    
    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, user: User = Depends(get_current_user)) -> User:
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted"
            )
        return user


# Convenience role checkers
require_admin = RoleChecker([UserRole.ADMIN])
require_analyst = RoleChecker([UserRole.ADMIN, UserRole.ANALYST])
require_viewer = RoleChecker([UserRole.ADMIN, UserRole.ANALYST, UserRole.VIEWER])

