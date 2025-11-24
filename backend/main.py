"""
Elite Creatif - FastAPI Backend
Production-grade multi-tenant SaaS API

🎓 TEACHING: API Structure
/api/v1/auth       - Authentication (register, login)
/api/v1/tenants    - Company management
/api/v1/campaigns  - Campaign CRUD
/api/v1/leads      - Lead management
/api/v1/automations - Automation pipeline
/docs              - Interactive API documentation (Swagger)
/redoc             - Alternative API documentation

Run:
    python backend/main.py
    Open: http://localhost:8000/docs
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env file BEFORE importing any modules that use environment variables
from pathlib import Path
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[INFO] Loaded environment from: {env_path}")
    else:
        print(f"[WARNING] .env file not found at: {env_path}")
except ImportError:
    print("[WARNING] python-dotenv not installed. Install with: pip install python-dotenv")
except Exception as e:
    print(f"[WARNING] Could not load .env file: {e}")

from fastapi import FastAPI, Depends, HTTPException, status, Body, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

import jwt
import torch

from backend import schemas
from backend.dependencies import get_db, get_current_user, get_current_tenant
from backend.auth import hash_password, verify_password, create_token_pair, SECRET_KEY, ALGORITHM
from backend.middleware import RateLimitMiddleware, RequestLoggingMiddleware, SecurityHeadersMiddleware
from backend.services.monitoring import monitoring_service
from backend.services.ai_service import ai_service
from backend.services.email_sender_service import email_sender_service
from backend.services.automation_service import get_automation_service
from models.tenant import Tenant
from models.user import User, UserRole
from models.campaign import Campaign, CampaignLead, EmailTemplate, EmailLog, EmailSendStatus
from models.base import init_db
from env_validator import run_all_validations
import uuid
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# Environment Validation
# ============================================================================

# Validate environment variables before starting the application
try:
    run_all_validations()
except Exception as e:
    print(f"[CRITICAL] Environment validation failed: {e}")
    sys.exit(1)

# ============================================================================
# Database Initialization
# ============================================================================

# Auto-initialize database on startup if tables don't exist
try:
    init_db()
    print("[OK] Database tables initialized/verified")
except Exception as e:
    print(f"[WARNING] Database initialization: {e}")

# ============================================================================
# FastAPI App Initialization
# ============================================================================

app = FastAPI(
    title="Elite Creatif API",
    description="Multi-tenant outreach automation platform",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration (allow frontend to call API)
# Get allowed origins from environment variable
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:7860")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Specific domains only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add Security Middleware (order matters - first added runs last)
app.add_middleware(RateLimitMiddleware)          # Rate limiting
app.add_middleware(RequestLoggingMiddleware)     # Request logging
app.add_middleware(SecurityHeadersMiddleware)    # Security headers


# ============================================================================
# AI Service Initialization
# ============================================================================

@app.on_event("startup")
async def initialize_ai_service():
    """
    Load AI model on server startup

    This takes 5-10 minutes on first run (downloads 14GB Qwen model)
    Subsequent starts are faster (loads from cache)
    """
    logger.info("Initializing AI service...")
    try:
        ai_service.load_model()
        logger.info("AI model loaded successfully!")
    except Exception as e:
        logger.error(f"Failed to load AI model: {e}")
        logger.warning("AI email generation features will be disabled")


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
def health_check():
    """
    Basic health check endpoint

    🎓 TEACHING: Why health checks?
    - Load balancers use this to know if server is alive
    - Monitoring systems ping this every 30 seconds
    - Returns 200 OK if everything is working
    """
    return {"status": "healthy", "version": "2.0.0"}


@app.get("/health/detailed")
def detailed_health_check():
    """
    Detailed health check with system metrics and application stats

    Returns:
    - Application uptime
    - Request/error counts
    - System resources (CPU, memory, disk)
    - Error rates
    """
    return monitoring_service.get_detailed_health()


@app.get("/metrics")
def get_metrics():
    """
    Prometheus-compatible metrics endpoint

    Returns application metrics for monitoring
    """
    health = monitoring_service.get_health_status()
    return {
        "uptime_seconds": health["uptime_seconds"],
        "total_requests": health["metrics"]["total_requests"],
        "total_errors": health["metrics"]["total_errors"],
        "error_rate": health["metrics"]["error_rate_percent"],
        "slow_requests": health["metrics"]["slow_requests"]
    }


# ============================================================================
# Notifications Routes
# ============================================================================

@app.get(
    "/api/v1/notifications",
    summary="Get user notifications",
    tags=["Notifications"]
)
def get_notifications(
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Get dynamic notifications based on recent activity

    Generates notifications from:
    - Recent campaigns and their leads
    - Email activity
    - System events
    """
    from datetime import datetime, timedelta

    notifications = []
    now = datetime.utcnow()

    # Get recent campaigns with leads
    recent_campaigns = db.query(Campaign).filter(
        Campaign.tenant_id == tenant.id
    ).order_by(Campaign.created_at.desc()).limit(10).all()

    for campaign in recent_campaigns:
        # Count leads in campaign
        lead_count = db.query(CampaignLead).filter(
            CampaignLead.campaign_id == campaign.id
        ).count()

        if lead_count > 0:
            # Calculate time ago
            time_diff = now - campaign.created_at
            if time_diff < timedelta(hours=1):
                time_ago = f"{int(time_diff.total_seconds() / 60)} minutes ago"
            elif time_diff < timedelta(days=1):
                time_ago = f"{int(time_diff.total_seconds() / 3600)} hours ago"
            elif time_diff < timedelta(days=7):
                time_ago = f"{int(time_diff.days)} days ago"
            else:
                time_ago = f"{int(time_diff.days / 7)} weeks ago"

            notifications.append({
                "id": f"campaign-{campaign.id}",
                "type": "leads_generated",
                "title": "New leads generated",
                "message": f'{lead_count} leads added to "{campaign.name}" campaign',
                "time_ago": time_ago,
                "campaign_id": campaign.id,
                "read": False
            })

    # Get recent email activity
    recent_emails = db.query(EmailLog).filter(
        EmailLog.tenant_id == tenant.id,
        EmailLog.sent_at.isnot(None)
    ).order_by(EmailLog.sent_at.desc()).limit(5).all()

    email_count = len(recent_emails)
    if email_count > 0:
        notifications.append({
            "id": "emails-recent",
            "type": "emails_sent",
            "title": "Emails sent",
            "message": f"{email_count} emails sent recently",
            "time_ago": "Recently",
            "read": False
        })

    # Sort by recency (campaigns are already sorted)
    # Limit to 5 notifications
    notifications = notifications[:5]

    # Add empty state if no notifications
    if not notifications:
        notifications.append({
            "id": "empty",
            "type": "info",
            "title": "No recent activity",
            "message": "Create a campaign to get started",
            "time_ago": "",
            "read": True
        })

    return {
        "notifications": notifications,
        "unread_count": sum(1 for n in notifications if not n.get("read", False))
    }


# ============================================================================
# Authentication Routes
# ============================================================================

@app.post(
    "/api/v1/auth/register",
    response_model=schemas.TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user and company",
    tags=["Authentication"]
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
    import uuid
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


@app.post(
    "/api/v1/auth/login",
    response_model=schemas.TokenResponse,
    summary="Login with email and password",
    tags=["Authentication"]
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
    from datetime import datetime
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


@app.post(
    "/api/v1/auth/refresh",
    response_model=schemas.TokenResponse,
    summary="Refresh access token",
    tags=["Authentication"]
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


@app.get(
    "/api/v1/auth/me",
    response_model=schemas.UserResponse,
    summary="Get current user profile",
    tags=["Authentication"]
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


# ============================================================================
# Tenant/Company Routes
# ============================================================================

@app.get(
    "/api/v1/tenants/me",
    response_model=schemas.TenantResponse,
    summary="Get current company profile",
    tags=["Tenants"]
)
def get_tenant_profile(
    tenant: Tenant = Depends(get_current_tenant)
):
    """Get currently logged-in user's company data"""
    return tenant


@app.patch(
    "/api/v1/tenants/me",
    response_model=schemas.TenantResponse,
    summary="Update company profile",
    tags=["Tenants"]
)
def update_tenant_profile(
    updates: schemas.TenantUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Update company profile

    🎓 TEACHING: Partial Updates
    - PATCH (not PUT) = only update provided fields
    - exclude_unset=True = ignore fields not in request
    """
    # Update only provided fields
    for field, value in updates.dict(exclude_unset=True).items():
        setattr(tenant, field, value)

    db.commit()
    db.refresh(tenant)
    return tenant


# ============================================================================
# Campaign Routes
# ============================================================================

@app.post(
    "/api/v1/campaigns",
    response_model=schemas.CampaignResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new campaign",
    tags=["Campaigns"]
)
def create_campaign(
    campaign_data: schemas.CampaignCreate,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Create new outreach campaign

    🎓 TEACHING: Tenant Isolation in Action
    - Campaign is automatically linked to current user's tenant
    - tenant_id comes from JWT token (not from request body)
    - This prevents user from creating campaigns for other companies
    """
    import uuid
    campaign = Campaign(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        **campaign_data.dict()
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


@app.get(
    "/api/v1/campaigns",
    response_model=list[schemas.CampaignResponse],
    summary="List all campaigns",
    tags=["Campaigns"]
)
def list_campaigns(
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Get all campaigns for current tenant

    🎓 TEACHING: Automatic Filtering
    - filter(Campaign.tenant_id == tenant.id) ensures isolation
    - Users ONLY see their own company's campaigns
    - No way to access other tenants' data
    """
    campaigns = db.query(Campaign).filter(
        Campaign.tenant_id == tenant.id
    ).order_by(Campaign.created_at.desc()).all()

    return campaigns


@app.get(
    "/api/v1/campaigns/{campaign_id}",
    response_model=schemas.CampaignResponse,
    summary="Get campaign details",
    tags=["Campaigns"]
)
def get_campaign(
    campaign_id: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get single campaign by ID"""
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.tenant_id == tenant.id  # CRITICAL: Ensure belongs to tenant
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    return campaign


@app.patch(
    "/api/v1/campaigns/{campaign_id}",
    response_model=schemas.CampaignResponse,
    summary="Update campaign",
    tags=["Campaigns"]
)
def update_campaign(
    campaign_id: str,
    updates: schemas.CampaignUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Update campaign details"""
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.tenant_id == tenant.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    # Update fields
    for field, value in updates.dict(exclude_unset=True).items():
        setattr(campaign, field, value)

    db.commit()
    db.refresh(campaign)
    return campaign


@app.delete(
    "/api/v1/campaigns/{campaign_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete campaign",
    tags=["Campaigns"]
)
def delete_campaign(
    campaign_id: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Delete campaign and all its leads"""
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.tenant_id == tenant.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    db.delete(campaign)
    db.commit()
    return None


# ============================================================================
# Lead Routes
# ============================================================================

@app.get(
    "/api/v1/campaigns/{campaign_id}/leads",
    response_model=list[schemas.LeadResponse],
    summary="Get campaign leads",
    tags=["Leads"]
)
def get_campaign_leads(
    campaign_id: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get all leads for a campaign"""
    # Verify campaign belongs to tenant
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.tenant_id == tenant.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    leads = db.query(CampaignLead).filter(
        CampaignLead.campaign_id == campaign_id
    ).all()

    return leads


@app.post(
    "/api/v1/campaigns/{campaign_id}/leads",
    response_model=schemas.LeadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add lead to campaign",
    tags=["Leads"]
)
def add_lead_to_campaign(
    campaign_id: str,
    lead_data: schemas.LeadCreate,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Add a single lead to a campaign"""
    # Verify campaign belongs to tenant
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.tenant_id == tenant.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    # Create lead
    import uuid
    lead = CampaignLead(
        id=str(uuid.uuid4()),
        campaign_id=campaign_id,
        **lead_data.dict()
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@app.post(
    "/api/v1/campaigns/{campaign_id}/leads/bulk",
    status_code=status.HTTP_201_CREATED,
    summary="Add multiple leads to campaign",
    tags=["Leads"]
)
def add_leads_bulk(
    campaign_id: str,
    leads_data: list[schemas.LeadCreate],
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Add multiple leads to a campaign at once"""
    # Verify campaign belongs to tenant
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.tenant_id == tenant.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    # Create leads in bulk
    import uuid
    leads = []
    for lead_data in leads_data:
        lead = CampaignLead(
            id=str(uuid.uuid4()),
            campaign_id=campaign_id,
            **lead_data.dict()
        )
        leads.append(lead)
        db.add(lead)

    db.commit()

    return {
        "message": f"Successfully added {len(leads)} leads to campaign",
        "campaign_id": campaign_id,
        "leads_added": len(leads)
    }


@app.post(
    "/api/v1/campaigns/{campaign_id}/upload-leads",
    status_code=status.HTTP_201_CREATED,
    summary="Upload leads from CSV/Excel file",
    tags=["Leads"]
)
async def upload_leads_file(
    campaign_id: str,
    file: UploadFile,
    generate_descriptions: bool = False,
    generate_emails: bool = False,
    company_info: str = None,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Upload leads from CSV or Excel file

    Required columns (flexible naming):
    - name/title/company/business_name
    - email (optional)
    - phone (optional)
    - address/location (optional)
    - website/url (optional)

    Optional AI enrichment:
    - generate_descriptions: Create AI business descriptions
    - generate_emails: Generate personalized outreach emails
    """
    import pandas as pd
    import io
    from datetime import datetime

    # Verify campaign belongs to tenant
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.tenant_id == tenant.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    # Check file type
    filename = file.filename.lower()
    if not (filename.endswith('.csv') or filename.endswith('.xlsx') or filename.endswith('.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be CSV or Excel format (.csv, .xlsx, .xls)"
        )

    try:
        # Read file content
        contents = await file.read()

        # Parse based on file type
        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))

        if df.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )

        # Normalize column names (lowercase, strip spaces)
        df.columns = df.columns.str.lower().str.strip()

        # Debug: Print DataFrame info
        print(f"[DEBUG] CSV columns after normalization: {list(df.columns)}")
        print(f"[DEBUG] DataFrame shape: {df.shape}")
        print(f"[DEBUG] First few rows:\n{df.head()}")

        # ============================================================================
        # HYBRID APPROACH: Predefined mapping FIRST, then AI fallback
        # ============================================================================

        # Step 1: Try predefined mapping (fast path)
        predefined_mapping = {
            'name': ['name', 'title', 'company', 'business_name', 'company_name', 'business'],
            'email': ['email', 'email_address', 'mail', 'e-mail'],
            'phone': ['phone', 'phone_number', 'tel', 'telephone', 'mobile', 'contact'],
            'address': ['address', 'location', 'city', 'area'],
            'website': ['website', 'url', 'web', 'site', 'link'],
            'generated_email': ['generated_email', 'ai email', 'ai_email', 'email_content', 'email_body']
        }

        # Description columns to merge (all variations)
        description_variations = [
            'description', 'ai description', 'ai_description', 'business_description',
            'about', 'summary', 'notes', 'details', 'info', 'bio', 'overview',
            'company_description', 'business_info', 'profile', 'background'
        ]

        mapped_columns = {}
        for target_col, possible_names in predefined_mapping.items():
            for col in df.columns:
                if col in possible_names:
                    mapped_columns[target_col] = col
                    break

        # Find ALL description-like columns to merge
        description_columns_found = [col for col in df.columns if col in description_variations]
        print(f"[DEBUG] Description columns found to merge: {description_columns_found}")

        print(f"[DEBUG] Predefined mapping result: {mapped_columns}")

        # Step 2: If 'name' not found, use AI to intelligently map columns
        additional_context_fields = []
        if 'name' not in mapped_columns:
            print("[INFO] Name column not found in predefined mapping, using AI...")

            try:
                # Get sample rows for AI analysis
                sample_rows = df.head(2).to_dict('records')

                # Use AI to analyze columns
                ai_mapping = ai_service.analyze_csv_columns(
                    headers=list(df.columns),
                    sample_rows=sample_rows
                )

                # Merge AI mapping with any existing predefined mappings
                if 'field_mapping' in ai_mapping:
                    for field, csv_col in ai_mapping['field_mapping'].items():
                        if csv_col and csv_col in df.columns:
                            mapped_columns[field] = csv_col

                # Get additional context fields identified by AI
                if 'additional_context_fields' in ai_mapping:
                    additional_context_fields = [
                        col for col in ai_mapping['additional_context_fields']
                        if col in df.columns
                    ]

                print(f"[INFO] AI mapping complete: {mapped_columns}")
                print(f"[INFO] Additional context fields: {additional_context_fields}")

            except Exception as e:
                print(f"[WARNING] AI column mapping failed: {e}")
                # Continue with whatever mapping we have

        # Step 3: Validate required 'name' field
        if 'name' not in mapped_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not find name/title column. Available columns: {', '.join(df.columns)}. Please ensure your CSV has a column for company/business name."
            )

        # Process leads
        leads_created = []
        leads_failed = []

        for idx, row in df.iterrows():
            try:
                # Extract data with fallbacks
                lead_data = {
                    'title': str(row[mapped_columns['name']]).strip() if pd.notna(row[mapped_columns['name']]) else None,
                    'email': str(row[mapped_columns.get('email', 'email')]).strip() if 'email' in mapped_columns and pd.notna(row[mapped_columns['email']]) else None,
                    'phone': str(row[mapped_columns.get('phone', 'phone')]).strip() if 'phone' in mapped_columns and pd.notna(row[mapped_columns['phone']]) else None,
                    'address': str(row[mapped_columns.get('address', 'address')]).strip() if 'address' in mapped_columns and pd.notna(row[mapped_columns['address']]) else None,
                    'website': str(row[mapped_columns.get('website', 'website')]).strip() if 'website' in mapped_columns and pd.notna(row[mapped_columns['website']]) else None,
                    'generated_email': str(row[mapped_columns.get('generated_email', 'generated_email')]).strip() if 'generated_email' in mapped_columns and pd.notna(row[mapped_columns['generated_email']]) else None,
                }

                # Merge ALL description-like columns into one rich description
                description_parts = []
                for desc_col in description_columns_found:
                    if desc_col in row.index and pd.notna(row[desc_col]):
                        value = str(row[desc_col]).strip()
                        if value and value != 'nan':
                            # Add column name as context if multiple descriptions
                            if len(description_columns_found) > 1:
                                description_parts.append(f"[{desc_col}]: {value}")
                            else:
                                description_parts.append(value)

                # Join all description parts
                if description_parts:
                    lead_data['description'] = '\n\n'.join(description_parts)
                else:
                    lead_data['description'] = None

                # Skip if no title
                if not lead_data['title'] or lead_data['title'] == 'nan':
                    leads_failed.append({
                        'row': idx + 1,
                        'reason': 'Missing company name'
                    })
                    continue

                # Extract ALL additional context fields for email personalization
                additional_data = {}
                all_mapped_columns = set(mapped_columns.values())

                for col in additional_context_fields:
                    if col not in all_mapped_columns and col in row.index:
                        val = row[col]
                        if pd.notna(val):
                            additional_data[col] = str(val).strip()

                # Also extract any unmapped columns that have data
                for col in df.columns:
                    if col not in all_mapped_columns and col not in additional_context_fields and col in row.index:
                        val = row[col]
                        if pd.notna(val) and str(val).strip() and str(val).strip() != 'nan':
                            additional_data[col] = str(val).strip()

                # Create lead with ALL available data
                lead = CampaignLead(
                    id=str(uuid.uuid4()),
                    campaign_id=campaign_id,
                    title=lead_data['title'],
                    email=lead_data['email'],
                    phone=lead_data['phone'],
                    address=lead_data['address'],
                    website=lead_data['website'],
                    description=lead_data.get('description'),
                    generated_email=lead_data.get('generated_email'),
                    contact_source='file_upload',
                    lead_score=75 if lead_data.get('description') else 0,  # Higher score if description exists
                    email_sent=False,
                    scraped_data=additional_data if additional_data else None,  # Store ALL extra fields
                    created_at=datetime.utcnow()
                )

                db.add(lead)
                leads_created.append(lead)

            except Exception as e:
                leads_failed.append({
                    'row': idx + 1,
                    'reason': str(e)
                })

        # Commit all leads
        db.commit()

        # AI Enrichment (if requested)
        enrichment_stats = {
            'descriptions_generated': 0,
            'emails_generated': 0,
            'descriptions_from_csv': 0,
            'emails_from_csv': 0
        }

        if generate_descriptions or generate_emails:
            try:
                # Import AI service for business research generation
                from backend.services.ai_service import ai_service

                for lead in leads_created:
                    # Refresh to get DB state
                    db.refresh(lead)

                    # Generate business research using AI service (skip if already exists in CSV)
                    if generate_descriptions and not lead.description:
                        try:
                            description = ai_service.generate_business_research(
                                company_name=lead.title,
                                company_data=f"Address: {lead.address or 'N/A'}, Phone: {lead.phone or 'N/A'}, Website: {lead.website or 'N/A'}"
                            )
                            lead.description = description
                            lead.lead_score = 75  # Higher score for AI-researched leads
                            enrichment_stats['descriptions_generated'] += 1
                            print(f"[SUCCESS] Generated research for {lead.title}")
                        except Exception as e:
                            print(f"[ERROR] Failed to generate research for {lead.title}: {e}")
                    elif generate_descriptions and lead.description:
                        enrichment_stats['descriptions_from_csv'] += 1
                        print(f"[SKIP] Description already exists for {lead.title} (from CSV)")

                    # Generate personalized email using AI service (skip if already exists in CSV)
                    if generate_emails and company_info and not lead.generated_email:
                        try:
                            # Use the sophisticated email generation approach from generate_mail.py
                            import re

                            # Extract signature info from company_info
                            def extract_signature_info(text):
                                email_match = re.findall(r"[\w.-]+@[\w.-]+", text)
                                phone_match = re.findall(r"\+?\d[\d\s\-()]{7,}", text)
                                website_match = re.findall(r"www\.[\w.-]+", text)
                                company_name_match = re.search(r"We['']?re an? (.+?) offering", text, re.IGNORECASE)
                                name_match = re.search(r"Contact:\s*([^|\n]+)", text)

                                return {
                                    "name": name_match.group(1).strip() if name_match else "",
                                    "email": email_match[0] if email_match else "",
                                    "phone": phone_match[0] if phone_match else "",
                                    "website": website_match[0] if website_match else "",
                                    "company": company_name_match.group(1).strip() if company_name_match else ""
                                }

                            sig = extract_signature_info(company_info)

                            # Build comprehensive description using ALL available data
                            description = lead.description or f"{lead.title} - Business at {lead.address or 'N/A'}"

                            # Add ALL additional context from scraped_data for hyper-personalization
                            additional_context = ""
                            if lead.scraped_data:
                                context_items = []
                                for key, value in lead.scraped_data.items():
                                    if value and str(value).strip():
                                        formatted_key = key.replace('_', ' ').title()
                                        context_items.append(f"- {formatted_key}: {value}")
                                if context_items:
                                    additional_context = "\n\n**Additional Context:**\n" + "\n".join(context_items)

                            full_description = description + additional_context

                            first_name = lead.title.split()[0] if lead.title and ' ' in lead.title else None
                            company_title = lead.title or "there"
                            greeting = f"Dear {first_name}," if first_name else f"Dear {company_title} Team,"

                            # Comprehensive prompt with examples (from generate_mail.py)
                            base_instruction = f"""
You are an expert business email copywriter.
Your task: Write a professional, customized outreach email to a potential client, introducing the company and inviting them to collaborate or learn more about our services.

**Instructions:**
- Focus on the client's pain points and what makes our company unique.
- Be specific—no empty claims or clichés.
- End with a clear call to action (e.g., request a meeting, a reply, or a demo).
- The email must be ready to send with no placeholders or generic text.
- If a first name is provided, use it in the greeting; otherwise, use the company name.
- Maintain a friendly, engaging, and professional tone.
- End with your contact details from the info below.

## 📌 Example 1: (With First Name)
**Description:** "James Smith is the founder of SmithTech, a startup specializing in AI-powered business automation solutions."
**Generated Email:**
```
Subject: Let's Scale SmithTech with Smart Marketing

Dear James,

Your work in AI-driven business automation is truly exciting! At [Your Agency Name], we help innovative startups like SmithTech gain the visibility they deserve. Through SEO, strategic ad buying, and social media management, we ensure your solutions reach the right businesses.

Let's set up a quick call to explore how we can accelerate your brand's growth. Looking forward to collaborating!

Best regards,
[Your Name] | [Your Agency Name]
[Your Email] | [Your Website] | [Your Phone]
```

## 📌 Example 2: (Company Name Only)
**Description:** "Urban Trends is a modern fashion brand specializing in streetwear for young adults. They focus on sustainability and ethical production."
**Generated Email:**
```
Subject: Elevate Urban Trends' Online Presence

Dear Urban Trends Team,

We admire your commitment to sustainability and ethical fashion! At [Your Agency Name], we specialize in branding, social media management, and targeted advertising to help fashion brands reach their ideal audience.

With our expertise in SEO, PR, and influencer collaborations, we can amplify Urban Trends' presence and drive real engagement. Let's connect to discuss how we can grow your brand's impact!

Best regards,
[Your Name] | [Your Agency Name]
[Your Email] | [Your Website] | [Your Phone]
```"""

                            # Build messages for AI
                            messages = [
                                {
                                    "role": "system",
                                    "content": "You are an AI assistant specializing in crafting professional business emails for marketing purposes."
                                },
                                {
                                    "role": "user",
                                    "content": f"""
🔹 **Our Company Info:**
{company_info}

🔹 **Instructions:**
{base_instruction}

🔹 **Company Description & Context:**
{full_description}

🔹 **Greeting:**
{greeting}

Please follow the above instructions carefully and return only the generated email.
Use ALL the context provided above to create a highly personalized email that demonstrates you've researched this specific company.
"""
                                }
                            ]

                            # Apply chat template
                            text_prompt = ai_service.tokenizer.apply_chat_template(
                                messages,
                                tokenize=False,
                                add_generation_prompt=True
                            )

                            # Tokenize
                            model_inputs = ai_service.tokenizer(
                                [text_prompt],
                                return_tensors="pt"
                            ).to(ai_service.model.device)

                            # Generate with same parameters as generate_mail.py
                            with torch.no_grad():
                                generated_ids = ai_service.model.generate(
                                    **model_inputs,
                                    max_new_tokens=512,
                                    do_sample=True,
                                    temperature=0.9
                                )

                            # Decode
                            generated_text = ai_service.tokenizer.batch_decode(
                                generated_ids[:, model_inputs.input_ids.shape[1]:],
                                skip_special_tokens=True
                            )[0]

                            lead.generated_email = generated_text.strip()
                            enrichment_stats['emails_generated'] += 1
                            print(f"[SUCCESS] Generated email for {lead.title}")
                        except Exception as e:
                            print(f"[ERROR] Failed to generate email for {lead.title}: {e}")
                    elif generate_emails and lead.generated_email:
                        enrichment_stats['emails_from_csv'] += 1
                        print(f"[SKIP] Email already exists for {lead.title} (from CSV)")

                # Commit enrichments
                db.commit()

            except Exception as e:
                print(f"AI enrichment error: {e}")

        response_data = {
            "success": True,
            "message": f"Successfully uploaded {len(leads_created)} leads",
            "stats": {
                "total_rows": len(df),
                "leads_created": len(leads_created),
                "leads_failed": len(leads_failed),
                "descriptions_generated": enrichment_stats['descriptions_generated'],
                "descriptions_from_csv": enrichment_stats['descriptions_from_csv'],
                "emails_generated": enrichment_stats['emails_generated'],
                "emails_from_csv": enrichment_stats['emails_from_csv']
            },
            "failed_rows": leads_failed[:10] if leads_failed else [],  # Show first 10 failures
            "campaign_id": campaign_id
        }

        print(f"[DEBUG] Returning response: {response_data}")
        return response_data

    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty or malformed"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )


@app.post(
    "/api/v1/campaigns/{campaign_id}/generate-leads",
    status_code=status.HTTP_201_CREATED,
    summary="Generate leads from Google Maps",
    tags=["Leads"]
)
def generate_leads_google_maps(
    campaign_id: str,
    query: str,
    location: str = "",
    max_results: int = 50,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Generate leads from Google Maps Places API

    Uses real Google Maps API when configured, falls back to mock data for testing
    """
    from backend.services import search_places, GoogleMapsScraperError

    # Verify campaign belongs to tenant
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.tenant_id == tenant.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    try:
        # Search Google Maps for places
        places = search_places(
            query=query,
            location=location,
            max_results=max_results
        )

        # Convert to leads and save to database
        import uuid
        leads = []
        for place in places:
            lead = CampaignLead(
                id=str(uuid.uuid4()),
                campaign_id=campaign_id,
                title=place.get('title'),
                address=place.get('address'),
                phone=place.get('phone'),
                website=place.get('website'),
                description=f"Rating: {place.get('rating')}/5 ({place.get('reviews_count')} reviews)",
                lead_score=min(100, int(place.get('rating', 0) * 20)),  # Convert rating to score
                contact_source='google_maps',
                scraped_data=place  # Store original data as JSON
            )
            leads.append(lead)
            db.add(lead)

        db.commit()

        return {
            "message": f"Successfully generated {len(leads)} leads from Google Maps",
            "campaign_id": campaign_id,
            "leads_generated": len(leads),
            "query": query,
            "location": location
        }

    except GoogleMapsScraperError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate leads: {str(e)}"
        )


@app.post(
    "/api/v1/campaigns/{campaign_id}/generate-instagram-leads",
    status_code=status.HTTP_201_CREATED,
    summary="Generate leads from Instagram",
    tags=["Leads"]
)
def generate_leads_instagram(
    campaign_id: str,
    query: str,
    max_results: int = 30,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Generate leads from Instagram using SERPAPI

    Searches for Instagram profiles matching the query and extracts contact information
    """
    from backend.services.instagram_scraper import search_instagram_profiles, InstagramScraperError

    # Verify campaign belongs to tenant
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.tenant_id == tenant.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    try:
        # Search Instagram for profiles
        profiles = search_instagram_profiles(
            query=query,
            max_results=max_results
        )

        # Convert to leads and save to database
        import uuid
        leads = []
        for profile in profiles:
            # Calculate lead score based on contact availability
            has_email = bool(profile.get('email'))
            has_phone = bool(profile.get('phone'))
            has_website = bool(profile.get('website'))
            followers = profile.get('followers', 0)

            # Score: base 30 + email(20) + phone(20) + website(10) + followers bonus(up to 20)
            lead_score = 30
            if has_email:
                lead_score += 20
            if has_phone:
                lead_score += 20
            if has_website:
                lead_score += 10
            if followers > 10000:
                lead_score += 20
            elif followers > 1000:
                lead_score += 10

            lead = CampaignLead(
                id=str(uuid.uuid4()),
                campaign_id=campaign_id,
                title=profile.get('title'),
                address=profile.get('username', ''),
                phone=profile.get('phone', ''),
                email=profile.get('email', ''),
                website=profile.get('url'),
                description=profile.get('bio', ''),
                lead_score=min(lead_score, 100),  # Cap at 100
                contact_source='instagram',
                scraped_data={
                    'username': profile.get('username'),
                    'followers': profile.get('followers', 0),
                    'followers_display': profile.get('followers_display', ''),
                    'following': profile.get('following', 0),
                    'posts': profile.get('posts', 0),
                    'engagement_category': profile.get('engagement_category', ''),
                    'category': profile.get('category', ''),
                    'external_website': profile.get('website', ''),
                    'whatsapp': profile.get('whatsapp', ''),
                    'bio': profile.get('bio', ''),
                    'has_contact': profile.get('has_contact', False)
                }
            )
            leads.append(lead)
            db.add(lead)

        db.commit()

        return {
            "message": f"Successfully generated {len(leads)} leads from Instagram",
            "campaign_id": campaign_id,
            "leads_generated": len(leads),
            "query": query
        }

    except InstagramScraperError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate Instagram leads: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate Instagram leads: {str(e)}"
        )


@app.post(
    "/api/v1/campaigns/{campaign_id}/generate-linkedin-leads",
    status_code=status.HTTP_201_CREATED,
    summary="Generate leads from LinkedIn",
    tags=["Leads"]
)
def generate_leads_linkedin(
    campaign_id: str,
    query: str,
    max_results: int = 30,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Generate leads from LinkedIn using SERPAPI

    Searches for LinkedIn profiles matching the query and extracts contact information
    """
    from backend.services.linkedin_scraper import search_linkedin_profiles, LinkedInScraperError

    # Verify campaign belongs to tenant
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.tenant_id == tenant.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    try:
        # Search LinkedIn for profiles
        profiles = search_linkedin_profiles(
            query=query,
            max_results=max_results
        )

        # Convert to leads and save to database
        import uuid
        leads = []
        for profile in profiles:
            # Calculate lead score based on contact availability and seniority
            has_email = bool(profile.get('email'))
            has_phone = bool(profile.get('phone'))
            has_website = bool(profile.get('website'))
            connections = profile.get('connections', 0)
            seniority = profile.get('seniority', '')

            # Score: base 30 + email(20) + phone(20) + website(10) + connections/seniority bonus
            lead_score = 30
            if has_email:
                lead_score += 20
            if has_phone:
                lead_score += 20
            if has_website:
                lead_score += 10
            if connections > 500:
                lead_score += 10
            if 'Senior' in seniority or 'Executive' in seniority:
                lead_score += 10

            lead = CampaignLead(
                id=str(uuid.uuid4()),
                campaign_id=campaign_id,
                title=profile.get('title'),
                address=profile.get('location', ''),
                phone=profile.get('phone', ''),
                email=profile.get('email', ''),
                website=profile.get('url'),
                description=profile.get('bio', ''),
                lead_score=min(lead_score, 100),
                contact_source='linkedin',
                scraped_data={
                    'username': profile.get('username'),
                    'job_title': profile.get('job_title', ''),
                    'company': profile.get('company', ''),
                    'location': profile.get('location', ''),
                    'connections': profile.get('connections', 0),
                    'connections_display': profile.get('connections_display', ''),
                    'followers': profile.get('followers', 0),
                    'followers_display': profile.get('followers_display', ''),
                    'experience_years': profile.get('experience_years', 0),
                    'seniority': profile.get('seniority', ''),
                    'industry': profile.get('industry', ''),
                    'external_website': profile.get('website', ''),
                    'bio': profile.get('bio', ''),
                    'has_contact': profile.get('has_contact', False)
                }
            )
            leads.append(lead)
            db.add(lead)

        db.commit()

        return {
            "message": f"Successfully generated {len(leads)} leads from LinkedIn",
            "campaign_id": campaign_id,
            "leads_generated": len(leads),
            "query": query
        }

    except LinkedInScraperError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate LinkedIn leads: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate LinkedIn leads: {str(e)}"
        )


@app.post(
    "/api/v1/campaigns/{campaign_id}/leads/enrich",
    status_code=status.HTTP_200_OK,
    summary="Enrich leads by scraping their websites",
    tags=["Leads"]
)
def enrich_leads_from_websites(
    campaign_id: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Enrich all leads in a campaign by visiting their websites and extracting contact information

    This will:
    - Visit each lead's website
    - Check contact pages
    - Extract emails, phones, WhatsApp, and social links
    - Update the lead records with found information
    """
    from backend.services.website_scraper import scrape_website_contacts

    # Verify campaign belongs to tenant
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.tenant_id == tenant.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    # Get all leads in the campaign
    leads = db.query(CampaignLead).filter(
        CampaignLead.campaign_id == campaign_id
    ).all()

    if not leads:
        return {
            "message": "No leads found in this campaign",
            "campaign_id": campaign_id,
            "leads_enriched": 0
        }

    enriched_count = 0
    emails_found = 0
    phones_found = 0
    skipped_count = 0
    errors = []

    for lead in leads:
        # Get website URL
        website = lead.website

        # Skip if it's just an Instagram/LinkedIn profile URL
        if website and any(social in website.lower() for social in ['instagram.com', 'linkedin.com']):
            # Try to get external website from scraped_data
            if lead.scraped_data and lead.scraped_data.get('external_website'):
                website = lead.scraped_data['external_website']
            else:
                skipped_count += 1
                continue

        if not website:
            skipped_count += 1
            continue

        try:
            # Scrape the website
            result = scrape_website_contacts(website, follow_contact_page=True)

            if not result.get('success'):
                errors.append(f"{lead.title}: {result.get('error', 'Unknown error')}")
                continue

            updated = False

            # Update email if found
            if result.get('emails'):
                existing_emails = set(lead.email.split('; ')) if lead.email else set()
                new_emails = set(result['emails']) - existing_emails
                if new_emails:
                    all_emails = list(existing_emails | new_emails)
                    lead.email = '; '.join([e for e in all_emails if e])[:500]
                    emails_found += len(new_emails)
                    updated = True

            # Update phone if found
            if result.get('phones'):
                existing_phones = set(lead.phone.split('; ')) if lead.phone else set()
                new_phones = set(result['phones']) - existing_phones
                if new_phones:
                    all_phones = list(existing_phones | new_phones)
                    lead.phone = '; '.join([p for p in all_phones if p])[:200]
                    phones_found += len(new_phones)
                    updated = True

            # Update scraped_data with additional info
            if not lead.scraped_data:
                lead.scraped_data = {}

            if result.get('whatsapp'):
                lead.scraped_data['whatsapp'] = result['whatsapp']
                updated = True

            if result.get('social'):
                lead.scraped_data['social_links'] = result['social']
                updated = True

            lead.scraped_data['website_enriched'] = True
            lead.scraped_data['pages_checked'] = result.get('pages_checked', 1)

            # Update lead score if we found new contact info
            if updated:
                # Recalculate lead score
                has_email = bool(lead.email)
                has_phone = bool(lead.phone)
                has_whatsapp = bool(lead.scraped_data.get('whatsapp'))

                score = 30
                if has_email:
                    score += 25
                if has_phone:
                    score += 25
                if has_whatsapp:
                    score += 10
                if lead.scraped_data.get('social_links'):
                    score += 10

                lead.lead_score = min(score, 100)
                enriched_count += 1

            # Mark the ORM object as modified
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(lead, 'scraped_data')

        except Exception as e:
            errors.append(f"{lead.title}: {str(e)}")
            continue

    db.commit()

    return {
        "message": f"Successfully enriched {enriched_count} leads from websites",
        "campaign_id": campaign_id,
        "enriched": enriched_count,
        "total_leads": len(leads),
        "emails_found": emails_found,
        "phones_found": phones_found,
        "skipped": skipped_count,
        "errors": errors[:10] if errors else []  # Return first 10 errors
    }


@app.post(
    "/api/v1/leads/{lead_id}/enrich",
    status_code=status.HTTP_200_OK,
    summary="Enrich a single lead by scraping its website",
    tags=["Leads"]
)
def enrich_single_lead(
    lead_id: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Enrich a single lead by visiting its website and extracting contact information
    """
    from backend.services.website_scraper import scrape_website_contacts

    # Get the lead and verify ownership
    lead = db.query(CampaignLead).join(Campaign).filter(
        CampaignLead.id == lead_id,
        Campaign.tenant_id == tenant.id
    ).first()

    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )

    # Get website URL
    website = lead.website

    # Try external website from scraped_data if main website is social media
    if website and any(social in website.lower() for social in ['instagram.com', 'linkedin.com']):
        if lead.scraped_data and lead.scraped_data.get('external_website'):
            website = lead.scraped_data['external_website']

    if not website:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No website URL available for this lead"
        )

    # Scrape the website
    result = scrape_website_contacts(website, follow_contact_page=True)

    if not result.get('success'):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scrape website: {result.get('error', 'Unknown error')}"
        )

    # Update lead with found information
    if result.get('emails'):
        existing_emails = set(lead.email.split('; ')) if lead.email else set()
        all_emails = list(existing_emails | set(result['emails']))
        lead.email = '; '.join([e for e in all_emails if e])[:500]

    if result.get('phones'):
        existing_phones = set(lead.phone.split('; ')) if lead.phone else set()
        all_phones = list(existing_phones | set(result['phones']))
        lead.phone = '; '.join([p for p in all_phones if p])[:200]

    if not lead.scraped_data:
        lead.scraped_data = {}

    if result.get('whatsapp'):
        lead.scraped_data['whatsapp'] = result['whatsapp']

    if result.get('social'):
        lead.scraped_data['social_links'] = result['social']

    lead.scraped_data['website_enriched'] = True
    lead.scraped_data['pages_checked'] = result.get('pages_checked', 1)

    # Recalculate lead score
    has_email = bool(lead.email)
    has_phone = bool(lead.phone)
    has_whatsapp = bool(lead.scraped_data.get('whatsapp'))

    score = 30
    if has_email:
        score += 25
    if has_phone:
        score += 25
    if has_whatsapp:
        score += 10
    if lead.scraped_data.get('social_links'):
        score += 10

    lead.lead_score = min(score, 100)

    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(lead, 'scraped_data')

    db.commit()

    return {
        "message": "Lead enriched successfully",
        "lead_id": lead_id,
        "emails_found": len(result.get('emails', [])),
        "phones_found": len(result.get('phones', [])),
        "whatsapp_found": bool(result.get('whatsapp')),
        "social_links_found": list(result.get('social', {}).keys())
    }


# ============================================================================
# Dashboard Routes
# ============================================================================

@app.get(
    "/api/v1/dashboard/stats",
    response_model=schemas.DashboardStats,
    summary="Get dashboard statistics",
    tags=["Dashboard"]
)
def get_dashboard_stats(
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Get aggregated statistics for dashboard

    Returns counts for campaigns, leads, and engagement metrics
    """
    from sqlalchemy import func
    from datetime import datetime, timedelta

    # Get campaign counts
    total_campaigns = db.query(func.count(Campaign.id)).filter(
        Campaign.tenant_id == tenant.id
    ).scalar() or 0

    active_campaigns = db.query(func.count(Campaign.id)).filter(
        Campaign.tenant_id == tenant.id,
        Campaign.status == 'active'
    ).scalar() or 0

    # Get lead counts
    total_leads = db.query(func.count(CampaignLead.id)).join(
        Campaign, Campaign.id == CampaignLead.campaign_id
    ).filter(
        Campaign.tenant_id == tenant.id
    ).scalar() or 0

    # Get leads this month
    first_day_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    leads_this_month = db.query(func.count(CampaignLead.id)).join(
        Campaign, Campaign.id == CampaignLead.campaign_id
    ).filter(
        Campaign.tenant_id == tenant.id,
        CampaignLead.created_at >= first_day_of_month
    ).scalar() or 0

    # Get leads last month
    first_day_last_month = (first_day_of_month - timedelta(days=1)).replace(day=1)
    leads_last_month = db.query(func.count(CampaignLead.id)).join(
        Campaign, Campaign.id == CampaignLead.campaign_id
    ).filter(
        Campaign.tenant_id == tenant.id,
        CampaignLead.created_at >= first_day_last_month,
        CampaignLead.created_at < first_day_of_month
    ).scalar() or 0

    # Get email stats
    emails_sent = db.query(func.count(CampaignLead.id)).join(
        Campaign, Campaign.id == CampaignLead.campaign_id
    ).filter(
        Campaign.tenant_id == tenant.id,
        CampaignLead.email_sent == True
    ).scalar() or 0

    # Calculate response rate (leads that replied / emails sent)
    emails_replied = db.query(func.count(CampaignLead.id)).join(
        Campaign, Campaign.id == CampaignLead.campaign_id
    ).filter(
        Campaign.tenant_id == tenant.id,
        CampaignLead.replied == True
    ).scalar() or 0

    response_rate = (emails_replied / emails_sent * 100) if emails_sent > 0 else 0.0

    return schemas.DashboardStats(
        total_leads=total_leads,
        total_campaigns=total_campaigns,
        active_campaigns=active_campaigns,
        emails_sent=emails_sent,
        response_rate=round(response_rate, 1),
        leads_this_month=leads_this_month,
        leads_last_month=leads_last_month
    )


# ============================================================================
# Team/User Management Routes
# ============================================================================

@app.get(
    "/api/v1/team/members",
    response_model=list[schemas.TeamMemberResponse],
    summary="List team members",
    tags=["Team"]
)
def list_team_members(
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all users in the current tenant

    Returns list of team members with their roles and status
    """
    users = db.query(User).filter(
        User.tenant_id == tenant.id
    ).order_by(User.created_at.desc()).all()

    return users


@app.post(
    "/api/v1/team/invite",
    response_model=schemas.TeamMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite new team member",
    tags=["Team"]
)
def invite_team_member(
    invite_data: schemas.UserInvite,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Invite a new user to join the tenant

    Only admins and owners can invite users
    Creates user account and sends invitation email
    """
    from models.user import UserRole

    # Check permissions - only admin or owner can invite
    if current_user.role not in [UserRole.ADMIN, UserRole.OWNER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and owners can invite team members"
        )

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == invite_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    # Create temporary password (in production, send email with invitation link)
    import secrets
    temp_password = secrets.token_urlsafe(16)
    hashed_password = hash_password(temp_password)

    # Create new user
    import uuid
    new_user = User(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        email=invite_data.email,
        hashed_password=hashed_password,
        first_name=invite_data.first_name,
        last_name=invite_data.last_name,
        role=UserRole[invite_data.role.upper()],
        is_active=True,
        email_verified=False
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Send invitation email
    try:
        from backend.services.email_service import send_team_invitation
        send_team_invitation(
            to_email=invite_data.email,
            inviter_name=current_user.full_name,
            company_name=tenant.name,
            role=invite_data.role,
            temp_password=temp_password
        )
        logger.info(f"Invitation email sent to {invite_data.email}")
    except Exception as e:
        logger.warning(f"Failed to send invitation email: {e}")
        # Don't fail the request if email fails

    return new_user


@app.patch(
    "/api/v1/team/{user_id}/role",
    response_model=schemas.TeamMemberResponse,
    summary="Update team member role",
    tags=["Team"]
)
def update_team_member_role(
    user_id: str,
    role_update: schemas.UserRoleUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a team member's role

    Only owners can change roles
    Cannot change the owner role
    """
    from models.user import UserRole

    # Only owners can change roles
    if current_user.role != UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can change user roles"
        )

    # Get target user
    target_user = db.query(User).filter(
        User.id == user_id,
        User.tenant_id == tenant.id
    ).first()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Cannot change owner role
    if target_user.role == UserRole.OWNER and role_update.role.lower() != "owner":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change owner role. Transfer ownership first."
        )

    # Cannot change your own role
    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )

    # Update role
    target_user.role = UserRole[role_update.role.upper()]
    db.commit()
    db.refresh(target_user)

    return target_user


@app.delete(
    "/api/v1/team/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove team member",
    tags=["Team"]
)
def remove_team_member(
    user_id: str,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove a user from the tenant

    Only admins and owners can remove users
    Cannot remove the owner
    """
    from models.user import UserRole

    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.OWNER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and owners can remove team members"
        )

    # Get target user
    target_user = db.query(User).filter(
        User.id == user_id,
        User.tenant_id == tenant.id
    ).first()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Cannot remove owner
    if target_user.role == UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the owner"
        )

    # Cannot remove yourself
    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove yourself"
        )

    # Delete user
    db.delete(target_user)
    db.commit()

    return {"message": "User removed successfully"}


# ============================================================================
# Email Template Routes
# ============================================================================

@app.post(
    "/api/v1/email-templates",
    response_model=schemas.EmailTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create email template",
    tags=["Email Templates"]
)
def create_email_template(
    template_data: schemas.EmailTemplateCreate,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Create new email template for AI personalization

    Templates can use variables like {{company_name}}, {{first_name}}
    AI will personalize based on lead data
    """
    template = EmailTemplate(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        **template_data.dict()
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@app.get(
    "/api/v1/email-templates",
    response_model=list[schemas.EmailTemplateResponse],
    summary="List email templates",
    tags=["Email Templates"]
)
def list_email_templates(
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get all email templates for current tenant"""
    templates = db.query(EmailTemplate).filter(
        EmailTemplate.tenant_id == tenant.id
    ).order_by(EmailTemplate.created_at.desc()).all()
    return templates


@app.get(
    "/api/v1/email-templates/{template_id}",
    response_model=schemas.EmailTemplateResponse,
    summary="Get email template",
    tags=["Email Templates"]
)
def get_email_template(
    template_id: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get single email template by ID"""
    template = db.query(EmailTemplate).filter(
        EmailTemplate.id == template_id,
        EmailTemplate.tenant_id == tenant.id
    ).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email template not found"
        )

    return template


@app.patch(
    "/api/v1/email-templates/{template_id}",
    response_model=schemas.EmailTemplateResponse,
    summary="Update email template",
    tags=["Email Templates"]
)
def update_email_template(
    template_id: str,
    updates: schemas.EmailTemplateUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Update email template"""
    template = db.query(EmailTemplate).filter(
        EmailTemplate.id == template_id,
        EmailTemplate.tenant_id == tenant.id
    ).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email template not found"
        )

    # Update fields
    for field, value in updates.dict(exclude_unset=True).items():
        setattr(template, field, value)

    db.commit()
    db.refresh(template)
    return template


@app.delete(
    "/api/v1/email-templates/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete email template",
    tags=["Email Templates"]
)
def delete_email_template(
    template_id: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Delete email template"""
    template = db.query(EmailTemplate).filter(
        EmailTemplate.id == template_id,
        EmailTemplate.tenant_id == tenant.id
    ).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email template not found"
        )

    db.delete(template)
    db.commit()
    return None


# ============================================================================
# AI Email Generation Routes
# ============================================================================

@app.post(
    "/api/v1/campaigns/{campaign_id}/generate-emails",
    response_model=schemas.GenerateEmailsResponse,
    summary="Generate AI-personalized emails for campaign leads",
    tags=["AI Email Generation"]
)
def generate_campaign_emails(
    campaign_id: str,
    request_data: schemas.GenerateEmailsRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Generate AI-personalized emails for all leads in campaign

    Uses Qwen 2.5-7B AI model to create unique, personalized emails
    for each lead based on their business information
    """
    # Verify campaign belongs to tenant
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.tenant_id == tenant.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    # Get email template
    template = db.query(EmailTemplate).filter(
        EmailTemplate.id == request_data.template_id,
        EmailTemplate.tenant_id == tenant.id
    ).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email template not found"
        )

    # Get leads without generated emails
    leads = db.query(CampaignLead).filter(
        CampaignLead.campaign_id == campaign_id,
        CampaignLead.generated_email.is_(None)  # Only leads without emails
    ).all()

    if not leads:
        return schemas.GenerateEmailsResponse(
            message="All leads already have generated emails",
            generated_count=0,
            failed_count=0,
            total=0
        )

    # Check if AI model is loaded
    if not ai_service.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI model is not loaded. Please try again in a few minutes."
        )

    # Generate emails using AI
    generated_count = 0
    failed_count = 0

    logger.info(f"Starting AI email generation for {len(leads)} leads...")

    for lead in leads:
        try:
            # Generate personalized email
            result = ai_service.generate_email(
                lead_name=lead.title or "Business",
                lead_title=lead.title or "Business",
                lead_description=lead.description or "",
                template_subject=template.subject,
                template_body=template.body,
                company_info=request_data.company_info,
                first_name=None
            )

            # Save generated email to lead
            lead.generated_email = f"Subject: {result['subject']}\n\n{result['body']}"
            generated_count += 1

            logger.info(f"✅ Generated email for {lead.title}")

        except Exception as e:
            failed_count += 1
            logger.error(f"❌ Failed to generate email for {lead.title}: {e}")

    # Update template usage counter
    template.times_used += generated_count

    # Commit all changes
    db.commit()

    logger.info(f"✅ Email generation complete: {generated_count} generated, {failed_count} failed")

    return schemas.GenerateEmailsResponse(
        message=f"Successfully generated {generated_count} emails",
        generated_count=generated_count,
        failed_count=failed_count,
        total=len(leads)
    )


@app.get(
    "/api/v1/campaigns/{campaign_id}/emails",
    response_model=list[schemas.EmailLogResponse],
    summary="Get generated emails for campaign",
    tags=["Campaigns", "Email"]
)
def get_campaign_emails(
    campaign_id: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Get all generated emails for a campaign's leads

    Returns all email logs including:
    - Subject lines
    - Email bodies
    - Send status
    - Timestamps
    """
    # Verify campaign belongs to tenant
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.tenant_id == tenant.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    # Get all email logs for this campaign
    emails = db.query(EmailLog).filter(
        EmailLog.campaign_id == campaign_id,
        EmailLog.tenant_id == tenant.id
    ).order_by(EmailLog.created_at.desc()).all()

    return emails


@app.patch(
    "/api/v1/emails/{email_id}",
    response_model=schemas.EmailLogResponse,
    summary="Update email content",
    tags=["Email"]
)
def update_email(
    email_id: str,
    subject: str,
    body: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Update email subject and body before sending

    Allows users to edit AI-generated emails
    """
    # Get email and verify ownership
    email = db.query(EmailLog).filter(
        EmailLog.id == email_id,
        EmailLog.tenant_id == tenant.id
    ).first()

    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )

    # Update email
    email.subject = subject
    email.body = body

    db.commit()
    db.refresh(email)

    return email


@app.patch(
    "/api/v1/leads/{lead_id}",
    response_model=schemas.LeadResponse,
    summary="Update lead description",
    tags=["Leads"]
)
def update_lead(
    lead_id: str,
    description: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Update lead's AI-generated description

    Allows users to refine business descriptions
    """
    # Get lead and verify ownership through campaign
    lead = db.query(CampaignLead).join(Campaign).filter(
        CampaignLead.id == lead_id,
        Campaign.tenant_id == tenant.id
    ).first()

    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )

    # Update description
    lead.description = description

    db.commit()
    db.refresh(lead)

    return lead


@app.put(
    "/api/v1/leads/{lead_id}",
    response_model=schemas.LeadResponse,
    summary="Update lead details",
    tags=["Leads"]
)
def update_lead_full(
    lead_id: str,
    lead_data: dict = Body(...),
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Update all lead details (title, email, phone, address, website, description)

    Allows users to edit lead information directly from the UI
    """
    # Get lead and verify ownership through campaign
    lead = db.query(CampaignLead).join(Campaign).filter(
        CampaignLead.id == lead_id,
        Campaign.tenant_id == tenant.id
    ).first()

    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )

    # Update fields if provided
    if 'title' in lead_data and lead_data['title']:
        lead.title = lead_data['title']
    if 'email' in lead_data:
        lead.email = lead_data['email']
    if 'phone' in lead_data:
        lead.phone = lead_data['phone']
    if 'address' in lead_data:
        lead.address = lead_data['address']
    if 'website' in lead_data:
        lead.website = lead_data['website']
    if 'description' in lead_data:
        lead.description = lead_data['description']
    if 'generated_email' in lead_data:
        lead.generated_email = lead_data['generated_email']

    db.commit()
    db.refresh(lead)

    return lead


@app.delete(
    "/api/v1/leads/{lead_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete lead",
    tags=["Leads"]
)
def delete_lead(
    lead_id: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Delete a lead from the database

    Permanently removes the lead and all associated data
    """
    # Get lead and verify ownership through campaign
    lead = db.query(CampaignLead).join(Campaign).filter(
        CampaignLead.id == lead_id,
        Campaign.tenant_id == tenant.id
    ).first()

    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )

    # Delete the lead
    db.delete(lead)
    db.commit()

    return None


# ============================================================================
# Background Task Functions for AI Generation
# ============================================================================

def generate_description_background_task(lead_id: str, tenant_id: str):
    """
    Background task to generate AI description for a lead
    Runs asynchronously without blocking the API
    """
    from backend.services.ai_service import ai_service
    from models.base import SessionLocal

    db = SessionLocal()
    try:
        lead = db.query(CampaignLead).join(Campaign).filter(
            CampaignLead.id == lead_id,
            Campaign.tenant_id == tenant_id
        ).first()

        if lead:
            logger.info(f"[Background] Generating AI description for lead: {lead.title}")
            description = ai_service.generate_business_research(
                company_name=lead.title,
                company_data=f"Address: {lead.address or 'N/A'}, Phone: {lead.phone or 'N/A'}, Website: {lead.website or 'N/A'}"
            )
            lead.description = description
            lead.lead_score = 75
            db.commit()
            logger.info(f"[Background] ✅ AI description generated for: {lead.title}")
        else:
            logger.warning(f"[Background] Lead {lead_id} not found")
    except Exception as e:
        logger.error(f"[Background] Failed to generate description for lead {lead_id}: {e}")
    finally:
        db.close()


def generate_email_background_task(lead_id: str, tenant_id: str, company_info: str):
    """
    Background task to generate AI email for a lead
    Runs asynchronously without blocking the API
    """
    from backend.services.ai_service import ai_service
    from models.base import SessionLocal
    import re

    db = SessionLocal()
    try:
        lead = db.query(CampaignLead).join(Campaign).filter(
            CampaignLead.id == lead_id,
            Campaign.tenant_id == tenant_id
        ).first()

        if lead:
            logger.info(f"[Background] Generating AI email for lead: {lead.title}")

            # Extract signature info
            def extract_signature_info(text):
                email_match = re.findall(r"[\w.-]+@[\w.-]+", text)
                phone_match = re.findall(r"\+?\d[\d\s\-()]{7,}", text)
                website_match = re.findall(r"www\.[\w.-]+", text)
                company_name_match = re.search(r"We['']?re an? (.+?) offering", text, re.IGNORECASE)
                name_match = re.search(r"Contact:\s*([^|\n]+)", text)

                return {
                    "name": name_match.group(1).strip() if name_match else "",
                    "email": email_match[0] if email_match else "",
                    "phone": phone_match[0] if phone_match else "",
                    "website": website_match[0] if website_match else "",
                    "company": company_name_match.group(1).strip() if company_name_match else ""
                }

            sig = extract_signature_info(company_info)

            # Build comprehensive description using ALL available data
            description = lead.description or f"{lead.title} - Business at {lead.address or 'N/A'}"

            # Add ALL additional context from scraped_data for hyper-personalization
            additional_context = ""
            if lead.scraped_data:
                context_items = []
                for key, value in lead.scraped_data.items():
                    if value and str(value).strip():
                        # Format the key nicely (e.g., "rating" -> "Rating")
                        formatted_key = key.replace('_', ' ').title()
                        context_items.append(f"- {formatted_key}: {value}")

                if context_items:
                    additional_context = "\n\n**Additional Context:**\n" + "\n".join(context_items)

            # Combine description with additional context
            full_description = description + additional_context

            first_name = lead.title.split()[0] if lead.title and ' ' in lead.title else None
            company_title = lead.title or "there"
            greeting = f"Dear {first_name}," if first_name else f"Dear {company_title} Team,"

            base_instruction = """
You are an expert business email copywriter.
Your task: Write a professional, customized outreach email to a potential client, introducing the company and inviting them to collaborate or learn more about our services.

**Instructions:**
- Focus on the client's pain points and what makes our company unique.
- Be specific—no empty claims or clichés.
- End with a clear call to action (e.g., request a meeting, a reply, or a demo).
- The email must be ready to send with no placeholders or generic text.
- If a first name is provided, use it in the greeting; otherwise, use the company name.
- Maintain a friendly, engaging, and professional tone.
- End with your contact details from the info below."""

            messages = [
                {
                    "role": "system",
                    "content": "You are an AI assistant specializing in crafting professional business emails for marketing purposes."
                },
                {
                    "role": "user",
                    "content": f"""
🔹 **Our Company Info:**
{company_info}

🔹 **Instructions:**
{base_instruction}

🔹 **Company Description & Context:**
{full_description}

🔹 **Greeting:**
{greeting}

Please follow the above instructions carefully and return only the generated email.
Use ALL the context provided above to create a highly personalized email that demonstrates you've researched this specific company."""
                }
            ]

            text_prompt = ai_service.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )

            model_inputs = ai_service.tokenizer(
                [text_prompt],
                return_tensors="pt"
            ).to(ai_service.model.device)

            with torch.no_grad():
                generated_ids = ai_service.model.generate(
                    **model_inputs,
                    max_new_tokens=512,
                    do_sample=True,
                    temperature=0.9
                )

            generated_text = ai_service.tokenizer.batch_decode(
                generated_ids[:, model_inputs.input_ids.shape[1]:],
                skip_special_tokens=True
            )[0]

            lead.generated_email = generated_text.strip()
            db.commit()
            logger.info(f"[Background] ✅ AI email generated for: {lead.title}")
        else:
            logger.warning(f"[Background] Lead {lead_id} not found")
    except Exception as e:
        logger.error(f"[Background] Failed to generate email for lead {lead_id}: {e}")
    finally:
        db.close()


@app.post(
    "/api/v1/leads/{lead_id}/generate-description",
    summary="Generate AI description for a lead (async)",
    tags=["Leads"]
)
async def generate_lead_description(
    lead_id: str,
    background_tasks: BackgroundTasks,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Queue AI description generation in the background

    Returns immediately with status "processing"
    The AI generation happens asynchronously without blocking
    """
    lead = db.query(CampaignLead).join(Campaign).filter(
        CampaignLead.id == lead_id,
        Campaign.tenant_id == tenant.id
    ).first()

    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")

    # Queue the background task
    background_tasks.add_task(
        generate_description_background_task,
        lead_id=lead_id,
        tenant_id=tenant.id
    )

    logger.info(f"Queued AI description generation for lead: {lead.title}")

    return {
        "status": "processing",
        "message": f"AI description generation queued for {lead.title}. This will take 10-20 minutes on CPU.",
        "lead_id": lead_id
    }


@app.post(
    "/api/v1/leads/{lead_id}/generate-email",
    summary="Generate AI email for a lead (async)",
    tags=["Leads"]
)
async def generate_lead_email(
    lead_id: str,
    background_tasks: BackgroundTasks,
    company_info: str = Body(..., embed=True),
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Queue AI email generation in the background

    Returns immediately with status "processing"
    The AI generation happens asynchronously without blocking
    """
    lead = db.query(CampaignLead).join(Campaign).filter(
        CampaignLead.id == lead_id,
        Campaign.tenant_id == tenant.id
    ).first()

    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")

    # Queue the background task
    background_tasks.add_task(
        generate_email_background_task,
        lead_id=lead_id,
        tenant_id=tenant.id,
        company_info=company_info
    )

    logger.info(f"Queued AI email generation for lead: {lead.title}")

    return {
        "status": "processing",
        "message": f"AI email generation queued for {lead.title}. This will take 15-25 minutes on CPU.",
        "lead_id": lead_id
    }


@app.delete(
    "/api/v1/campaigns/{campaign_id}/leads",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete all leads in campaign",
    tags=["Leads"]
)
def delete_all_campaign_leads(
    campaign_id: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Delete all leads in a campaign"""
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.tenant_id == tenant.id
    ).first()

    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    # Delete all leads in the campaign
    db.query(CampaignLead).filter(CampaignLead.campaign_id == campaign_id).delete()
    db.commit()

    return None


# ============================================================================
# Email Sending Routes
# ============================================================================

@app.post(
    "/api/v1/campaigns/{campaign_id}/send-emails",
    response_model=schemas.SendEmailsResponse,
    summary="Send emails to campaign leads",
    tags=["Email Sending"]
)
def send_campaign_emails(
    campaign_id: str,
    send_data: schemas.SendEmailsRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Send generated emails to all leads in campaign via Gmail SMTP

    Requires Gmail app password (not regular password)
    Includes automatic rate limiting to avoid spam filters
    """
    # Verify campaign belongs to tenant
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.tenant_id == tenant.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    # Test Gmail connection first
    connection_test = email_sender_service.test_connection(
        send_data.sender_email,
        send_data.sender_password
    )

    if not connection_test["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=connection_test["error"]
        )

    # Send emails
    try:
        result = email_sender_service.send_bulk_emails(
            campaign_id=campaign_id,
            sender_email=send_data.sender_email,
            sender_password=send_data.sender_password,
            db=db,
            min_delay=send_data.min_delay,
            max_delay=send_data.max_delay
        )

        return schemas.SendEmailsResponse(
            message=f"Sent {result['sent']} emails successfully",
            sent=result["sent"],
            failed=result["failed"],
            total=result["total"]
        )

    except Exception as e:
        logger.error(f"Error sending emails: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send emails: {str(e)}"
        )


@app.post(
    "/api/v1/test-email-connection",
    summary="Test Gmail SMTP connection",
    tags=["Email Sending"]
)
def test_email_connection(
    test_data: schemas.TestEmailConnectionRequest
):
    """
    Test Gmail SMTP connection and authentication

    Use this to verify your Gmail app password before sending emails
    """
    result = email_sender_service.test_connection(
        test_data.sender_email,
        test_data.sender_password
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )

    return {"message": result["message"]}


# ============================================================================
# Email Analytics Routes
# ============================================================================

@app.get(
    "/api/v1/campaigns/{campaign_id}/email-analytics",
    response_model=schemas.EmailAnalyticsResponse,
    summary="Get email campaign analytics",
    tags=["Email Analytics"]
)
def get_email_analytics(
    campaign_id: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Get email analytics for campaign

    Returns counts and rates for sent, opened, clicked, replied emails
    """
    # Verify campaign belongs to tenant
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.tenant_id == tenant.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    # Get email logs
    from sqlalchemy import func

    total_sent = db.query(func.count(EmailLog.id)).filter(
        EmailLog.campaign_id == campaign_id,
        EmailLog.status == EmailSendStatus.SENT
    ).scalar() or 0

    total_failed = db.query(func.count(EmailLog.id)).filter(
        EmailLog.campaign_id == campaign_id,
        EmailLog.status == EmailSendStatus.FAILED
    ).scalar() or 0

    total_opened = db.query(func.count(EmailLog.id)).filter(
        EmailLog.campaign_id == campaign_id,
        EmailLog.status == EmailSendStatus.OPENED
    ).scalar() or 0

    total_clicked = db.query(func.count(EmailLog.id)).filter(
        EmailLog.campaign_id == campaign_id,
        EmailLog.status == EmailSendStatus.CLICKED
    ).scalar() or 0

    total_replied = db.query(func.count(EmailLog.id)).filter(
        EmailLog.campaign_id == campaign_id,
        EmailLog.status == EmailSendStatus.REPLIED
    ).scalar() or 0

    # Calculate rates
    open_rate = (total_opened / total_sent * 100) if total_sent > 0 else 0.0
    click_rate = (total_clicked / total_sent * 100) if total_sent > 0 else 0.0
    reply_rate = (total_replied / total_sent * 100) if total_sent > 0 else 0.0

    return schemas.EmailAnalyticsResponse(
        total_sent=total_sent,
        total_opened=total_opened,
        total_clicked=total_clicked,
        total_replied=total_replied,
        total_failed=total_failed,
        open_rate=round(open_rate, 1),
        click_rate=round(click_rate, 1),
        reply_rate=round(reply_rate, 1)
    )


@app.get(
    "/api/v1/campaigns/{campaign_id}/email-logs",
    response_model=list[schemas.EmailLogResponse],
    summary="Get email logs for campaign",
    tags=["Email Analytics"]
)
def get_email_logs(
    campaign_id: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Get all email logs for campaign

    Returns detailed log of each email sent with status and timestamps
    """
    # Verify campaign belongs to tenant
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.tenant_id == tenant.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    # Get email logs
    logs = db.query(EmailLog).filter(
        EmailLog.campaign_id == campaign_id
    ).order_by(EmailLog.created_at.desc()).all()

    return logs


# ============================================================================
# Full Automation Pipeline Routes
# ============================================================================

@app.post(
    "/api/v1/campaigns/{campaign_id}/run-automation",
    response_model=schemas.RunAutomationResponse,
    summary="Run full automation pipeline",
    tags=["Automation"]
)
async def run_automation_pipeline(
    campaign_id: str,
    automation_data: schemas.RunAutomationRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Run the complete automation pipeline for a campaign:

    1. Scrape leads from Google Maps/LinkedIn/Instagram
    2. Generate AI descriptions for each business (optional)
    3. Generate AI-personalized emails (optional)
    4. Send emails automatically via Gmail (optional)

    This is the ONE-CLICK automation from the Gradio app, now integrated into the SaaS platform!

    Example:
    ```json
    {
        "query": "restaurants in Dubai Marina",
        "source": "google_maps",
        "max_results": 50,
        "generate_descriptions": true,
        "generate_emails": true,
        "template_id": "uuid-123",
        "company_info": "We help restaurants increase online visibility...",
        "auto_send_emails": false
    }
    ```
    """
    # Verify campaign belongs to tenant
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.tenant_id == tenant.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    # Validate: if generate_emails is true, company_info is required
    if automation_data.generate_emails:
        if not automation_data.company_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="company_info is required when generate_emails is true (AI needs to know about your business)"
            )

    # Validate: if auto_send_emails is true, sender credentials are required
    if automation_data.auto_send_emails:
        if not automation_data.sender_email or not automation_data.sender_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="sender_email and sender_password are required when auto_send_emails is true"
            )

    # Get automation service
    automation_service = get_automation_service(db, ai_service, email_sender_service)

    # Run automation
    try:
        result = await automation_service.run_full_automation(
            campaign_id=campaign_id,
            tenant_id=tenant.id,
            query=automation_data.query,
            source=automation_data.source,
            max_results=automation_data.max_results,
            generate_descriptions=automation_data.generate_descriptions,
            generate_emails=automation_data.generate_emails,
            company_info=automation_data.company_info,
            custom_instruction=automation_data.custom_instruction,
            auto_send_emails=automation_data.auto_send_emails,
            sender_email=automation_data.sender_email,
            sender_password=automation_data.sender_password,
            min_delay=automation_data.min_delay,
            max_delay=automation_data.max_delay
        )

        return schemas.RunAutomationResponse(**result)

    except Exception as e:
        logger.error(f"Automation pipeline failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Automation failed: {str(e)}"
        )


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("Elite Creatif API Server")
    print("=" * 60)
    print()
    print("Starting server...")
    print("  - API: http://localhost:8000")
    print("  - Docs: http://localhost:8000/docs")
    print("  - ReDoc: http://localhost:8000/redoc")
    print()
    print("=" * 60)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )

