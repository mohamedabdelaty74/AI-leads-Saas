"""
Authentication Routes
Handles user registration, login, token refresh, and profile retrieval
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
import jwt
import uuid
from datetime import datetime

from backend import schemas
from backend.dependencies import get_db, get_current_user
from backend.auth import hash_password, verify_password, create_token_pair, SECRET_KEY, ALGORITHM
from models.tenant import Tenant
from models.user import User, UserRole

# Create router with prefix
router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=schemas.TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user and company"
)
def register(
    user_data: schemas.UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register new user and create their company (tenant)

    🎓 TEACHING: Registration Flow
    1. Check if email already exists → reject if yes
    2. Create new Tenant (company)
    3. Create new User (set role=owner for first user)
    4. Generate JWT tokens
    5. Return tokens + user data

    This creates a complete isolated environment for the new customer.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check if company email already exists
    existing_tenant = db.query(Tenant).filter(
        Tenant.company_email == user_data.company_email
    ).first()
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company already registered"
        )

    # Create tenant (company)
    tenant_id = str(uuid.uuid4())
    tenant = Tenant(
        id=tenant_id,
        name=user_data.company_name,
        company_email=user_data.company_email,
        company_website=user_data.company_website,
        status="trial",  # Start with trial
        plan="starter",
        leads_quota=500,  # Starter plan limit
        leads_used=0
    )
    db.add(tenant)
    db.flush()  # Get tenant.id before creating user

    # Create user (first user is always 'owner')
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        tenant_id=tenant.id,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=UserRole.OWNER,  # First user is owner
        is_active=True,
        email_verified=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate tokens
    tokens = create_token_pair(
        user_id=str(user.id),
        tenant_id=str(tenant.id),
        role=user.role
    )

    return {
        **tokens,
        "user": user
    }


@router.post(
    "/login",
    response_model=schemas.TokenResponse,
    summary="Login with email and password"
)
def login(
    credentials: schemas.UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login with email and password

    🎓 TEACHING: Login Flow
    1. Find user by email
    2. Verify password (bcrypt comparison)
    3. Check if user is active
    4. Generate new JWT tokens
    5. Update last_login_at timestamp
    """
    # Find user
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Verify password
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()

    # Generate tokens
    tokens = create_token_pair(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        role=user.role
    )

    return {
        **tokens,
        "user": user
    }


@router.post(
    "/refresh",
    response_model=schemas.TokenResponse,
    summary="Refresh access token"
)
def refresh_token(
    refresh_token: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """
    Refresh access token using a valid refresh token

    Validates the refresh token and issues new access + refresh tokens
    """
    try:
        # Decode the refresh token
        payload = jwt.decode(
            refresh_token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        # Verify token type
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        # Extract user info
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        role = payload.get("role")

        if not user_id or not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        # Verify user still exists and is active
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # Generate new token pair
        tokens = create_token_pair(
            user_id=user_id,
            tenant_id=tenant_id,
            role=role
        )

        return {
            **tokens,
            "user": user
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.get(
    "/me",
    response_model=schemas.UserResponse,
    summary="Get current user profile"
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get currently logged-in user's profile

    🎓 TEACHING: Protected Route
    - Requires "Authorization: Bearer <token>" header
    - Depends(get_current_user) automatically validates token
    - If token is invalid/expired → 401 Unauthorized
    - If valid → returns user data
    """
    return current_user
