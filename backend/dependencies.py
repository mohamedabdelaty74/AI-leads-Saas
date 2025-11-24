"""
FastAPI Dependencies - Reusable components for routes

🎓 TEACHING: What are dependencies?
- Functions that run BEFORE your route handler
- Used for: authentication, database sessions, validation
- Keeps code DRY (Don't Repeat Yourself)

Example:
    @app.get("/campaigns")
    def get_campaigns(current_user: User = Depends(get_current_user)):
        # current_user is automatically injected
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.base import get_db_session
from models.user import User
from models.tenant import Tenant
from backend.auth import decode_access_token

# Security scheme for Swagger docs
security = HTTPBearer()


def get_db() -> Session:
    """
    Get database session

    🎓 TEACHING: Why use dependency?
    - Automatically opens DB connection
    - Automatically closes it when request finishes
    - Handles errors gracefully
    """
    db = next(get_db_session())
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Extract and validate current user from JWT token

    🎓 TEACHING: Flow
    1. Extract token from "Authorization: Bearer <token>" header
    2. Decode JWT token → get user_id
    3. Query database → get User object
    4. Return user (or raise 401 Unauthorized)

    Usage:
        @app.get("/me")
        def get_me(user: User = Depends(get_current_user)):
            return {"email": user.email}
    """
    # Extract token
    token = credentials.credentials

    # Decode token
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user


async def get_current_tenant(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Tenant:
    """
    Get current user's tenant

    🎓 TEACHING: Tenant Isolation
    - Every API call is scoped to ONE tenant
    - This prevents data leakage between customers
    - Core of multi-tenancy security

    Usage:
        @app.get("/campaigns")
        def get_campaigns(tenant: Tenant = Depends(get_current_tenant)):
            # tenant is automatically the logged-in user's company
            return tenant.campaigns
    """
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    if not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account suspended. Please contact support."
        )

    return tenant


def require_role(allowed_roles: list[str]):
    """
    Require specific role(s) to access endpoint

    🎓 TEACHING: Role-Based Access Control (RBAC)
    - owner: Full access (billing, delete account, etc.)
    - admin: Manage users and campaigns
    - member: View and create campaigns only

    Usage:
        @app.delete("/campaigns/{id}")
        def delete_campaign(
            campaign_id: str,
            user: User = Depends(require_role(["owner", "admin"]))
        ):
            # Only owners and admins can reach this code
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {', '.join(allowed_roles)}"
            )
        return current_user

    return role_checker


def check_tenant_quota(
    tenant: Tenant = Depends(get_current_tenant)
) -> Tenant:
    """
    Check if tenant has quota remaining

    🎓 TEACHING: Usage Limits
    - Prevent abuse (one user creating 1 million leads)
    - Enforce plan limits (Starter = 500 leads/month)
    - Upsell opportunity (show upgrade message)

    Usage:
        @app.post("/campaigns/{id}/leads")
        def create_lead(
            lead_data: dict,
            tenant: Tenant = Depends(check_tenant_quota)
        ):
            # This code only runs if tenant has quota
    """
    if not tenant.can_create_leads:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "message": "Monthly lead quota exceeded",
                "quota": tenant.leads_quota,
                "used": tenant.leads_used,
                "upgrade_url": "/billing/upgrade"
            }
        )

    return tenant
