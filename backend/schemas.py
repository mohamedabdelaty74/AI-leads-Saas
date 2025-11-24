"""
Pydantic schemas for request/response validation

🎓 TEACHING: Why Pydantic?
- Automatic validation (wrong type? Pydantic rejects it)
- Auto-generated API docs (Swagger shows examples)
- Type safety (IDE autocomplete works)
- Data conversion (string "123" → int 123 automatically)

Example:
    # Without Pydantic
    email = request.json.get("email")  # Could be None, wrong type, etc.

    # With Pydantic
    class UserCreate(BaseModel):
        email: str  # Guaranteed to be a string

    user = UserCreate(**request.json)  # Validated!
"""

from datetime import datetime
from typing import Optional, List, Union
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator, field_validator


# ============================================================================
# Authentication Schemas
# ============================================================================

class UserRegister(BaseModel):
    """
    Request body for user registration

    Example POST /api/v1/auth/register:
    {
        "company_name": "Acme Corp",
        "company_email": "info@acme.com",
        "email": "john@acme.com",
        "password": "SecurePass123!",
        "first_name": "John",
        "last_name": "Doe"
    }
    """
    # Tenant info (create new company)
    company_name: str = Field(..., min_length=2, max_length=255)
    company_email: EmailStr
    company_website: Optional[str] = None

    # User info
    email: EmailStr
    password: str = Field(..., min_length=8, description="At least 8 characters")
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    @validator('password')
    def password_strength(cls, v):
        """Ensure password has minimum complexity"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain a number')
        return v


class UserLogin(BaseModel):
    """Request body for login"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Response after successful login/register"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"


class UserResponse(BaseModel):
    """User data in API responses"""
    id: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    tenant_id: str
    is_active: bool
    created_at: datetime

    @field_validator('id', 'tenant_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        """Convert UUID objects from PostgreSQL to strings"""
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True  # Enable ORM mode


# ============================================================================
# Tenant/Company Schemas
# ============================================================================

class TenantResponse(BaseModel):
    """Tenant/Company data"""
    id: str
    name: str
    company_email: str
    company_website: Optional[str]
    status: str
    plan: str
    leads_quota: int
    leads_used: int
    created_at: datetime

    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        """Convert UUID objects from PostgreSQL to strings"""
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


class TenantUpdate(BaseModel):
    """Update tenant profile"""
    name: Optional[str] = None
    company_email: Optional[EmailStr] = None
    company_website: Optional[str] = None
    company_address: Optional[str] = None


# ============================================================================
# Campaign Schemas
# ============================================================================

class CampaignCreate(BaseModel):
    """
    Create new campaign

    Example POST /api/v1/campaigns:
    {
        "name": "Q1 Dubai Restaurants",
        "description": "Outreach to restaurants in Dubai",
        "search_query": "restaurants in Dubai Marina",
        "lead_source": "google_maps",
        "max_leads": 50,
        "description_style": "professional"
    }
    """
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    search_query: str
    lead_source: str = Field(..., pattern="^(google_maps|linkedin|instagram)$")
    max_leads: int = Field(10, ge=1, le=1000, description="1-1000 leads")
    description_style: str = Field("professional", pattern="^(professional|sales|casual)$")
    enable_ai_personalization: bool = True


class CampaignUpdate(BaseModel):
    """Update campaign"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(draft|active|paused|completed)$")


class CampaignResponse(BaseModel):
    """Campaign data in responses"""
    id: str
    tenant_id: str
    name: str
    description: Optional[str]
    status: str
    search_query: str
    lead_source: str
    max_leads: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    @field_validator('id', 'tenant_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        """Convert UUID objects from PostgreSQL to strings"""
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


# ============================================================================
# Lead Schemas
# ============================================================================

class LeadCreate(BaseModel):
    """Create/add a lead to a campaign"""
    title: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    description: Optional[str] = None
    lead_score: int = 50
    contact_source: Optional[str] = None
    scraped_data: Optional[dict] = None


class LeadResponse(BaseModel):
    """Individual lead data"""
    id: str
    campaign_id: str
    title: Optional[str]
    address: Optional[str]
    phone: Optional[str]
    website: Optional[str]
    email: Optional[str]
    description: Optional[str]
    lead_score: int
    generated_email: Optional[str]
    generated_whatsapp: Optional[str]
    email_sent: bool
    whatsapp_sent: bool
    replied: bool
    created_at: datetime

    @field_validator('id', 'campaign_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        """Convert UUID objects from PostgreSQL to strings"""
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


# ============================================================================
# Automation Pipeline Schemas
# ============================================================================

class AutomationRequest(BaseModel):
    """
    Request to start full automation pipeline

    Example POST /api/v1/automations/start:
    {
        "campaign_id": "uuid-123",
        "enable_descriptions": true,
        "enable_emails": true,
        "enable_whatsapp": false,
        "auto_send_email": false
    }
    """
    campaign_id: str
    enable_descriptions: bool = True
    enable_emails: bool = False
    enable_whatsapp: bool = False
    auto_send_email: bool = False
    auto_send_whatsapp: bool = False
    email_style: str = Field("professional", pattern="^(professional|sales|casual)$")


class AutomationStatus(BaseModel):
    """Status of running automation"""
    session_id: str
    status: str  # running, completed, failed
    progress: int  # 0-100
    current_step: str
    leads_extracted: int
    descriptions_generated: int
    emails_generated: int
    started_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]


# ============================================================================
# Dashboard Statistics Schemas
# ============================================================================

class DashboardStats(BaseModel):
    """Dashboard statistics"""
    total_leads: int
    total_campaigns: int
    active_campaigns: int
    emails_sent: int
    response_rate: float
    leads_this_month: int
    leads_last_month: int


# ============================================================================
# Team/User Management Schemas
# ============================================================================

class UserInvite(BaseModel):
    """Invite a new user to the tenant"""
    email: EmailStr
    role: str = Field(..., pattern="^(admin|member)$")
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserRoleUpdate(BaseModel):
    """Update user's role"""
    role: str = Field(..., pattern="^(owner|admin|member)$")


class TeamMemberResponse(BaseModel):
    """Team member data"""
    id: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime]

    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        """Convert UUID objects from PostgreSQL to strings"""
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


# ============================================================================
# Email Template Schemas
# ============================================================================

class EmailTemplateCreate(BaseModel):
    """Create new email template"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    subject: str = Field(..., min_length=1, max_length=500)
    body: str = Field(..., min_length=1)
    use_ai_personalization: bool = True


class EmailTemplateUpdate(BaseModel):
    """Update email template"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    subject: Optional[str] = Field(None, min_length=1, max_length=500)
    body: Optional[str] = Field(None, min_length=1)
    is_active: Optional[bool] = None
    use_ai_personalization: Optional[bool] = None


class EmailTemplateResponse(BaseModel):
    """Email template in responses"""
    id: str
    tenant_id: str
    name: str
    description: Optional[str]
    subject: str
    body: str
    is_active: bool
    use_ai_personalization: bool
    times_used: int
    created_at: datetime
    updated_at: datetime

    @field_validator('id', 'tenant_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


# ============================================================================
# Email Generation Schemas
# ============================================================================

class GenerateEmailsRequest(BaseModel):
    """Request to generate AI emails for campaign"""
    template_id: str
    company_info: str = Field(..., min_length=10, description="Your company information for AI context")


class GenerateEmailsResponse(BaseModel):
    """Response after generating emails"""
    message: str
    generated_count: int
    failed_count: int
    total: int


# ============================================================================
# Email Sending Schemas
# ============================================================================

class SendEmailsRequest(BaseModel):
    """Request to send emails to campaign leads"""
    sender_email: EmailStr
    sender_password: str = Field(..., min_length=1, description="Gmail app password")
    min_delay: int = Field(5, ge=1, le=60, description="Min delay between emails (seconds)")
    max_delay: int = Field(15, ge=1, le=120, description="Max delay between emails (seconds)")


class SendEmailsResponse(BaseModel):
    """Response after sending emails"""
    message: str
    sent: int
    failed: int
    total: int


class TestEmailConnectionRequest(BaseModel):
    """Test Gmail connection"""
    sender_email: EmailStr
    sender_password: str


# ============================================================================
# Email Analytics Schemas
# ============================================================================

class EmailAnalyticsResponse(BaseModel):
    """Email campaign analytics"""
    total_sent: int
    total_opened: int
    total_clicked: int
    total_replied: int
    total_failed: int
    open_rate: float
    click_rate: float
    reply_rate: float


class EmailLogResponse(BaseModel):
    """Single email log entry"""
    id: str
    lead_id: str
    campaign_id: str
    recipient_email: str
    subject: str
    status: str
    sent_at: Optional[datetime]
    opened_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime

    @field_validator('id', 'lead_id', 'campaign_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


# ============================================================================
# Full Automation Pipeline Schemas
# ============================================================================

class RunAutomationRequest(BaseModel):
    """
    Request to run the full automation pipeline

    Example POST /api/v1/campaigns/{campaign_id}/run-automation:
    {
        "query": "restaurants in Dubai",
        "source": "google_maps",
        "max_results": 50,
        "generate_descriptions": true,
        "generate_emails": true,
        "company_info": "We are Elite Creatif, a digital marketing agency specializing in SEO and social media for restaurants...",
        "custom_instruction": "Focus on how we can help increase online visibility and customer engagement",
        "auto_send_emails": false,
        "sender_email": "your@gmail.com",
        "sender_password": "app-password",
        "min_delay": 5,
        "max_delay": 15
    }
    """
    query: str = Field(..., min_length=1, description="Search query for lead scraping")
    source: str = Field("google_maps", pattern="^(google_maps|linkedin|instagram)$")
    max_results: int = Field(10, ge=1, le=500, description="Max leads to scrape")
    generate_descriptions: bool = Field(True, description="Generate AI business descriptions")
    generate_emails: bool = Field(True, description="Generate fully custom AI emails (NO templates needed!)")
    company_info: Optional[str] = Field(None, description="Your company info - AI uses this to create custom emails for each business")
    custom_instruction: Optional[str] = Field(None, description="Optional: Additional instructions for email tone/style")
    auto_send_emails: bool = Field(False, description="Automatically send emails after generation")
    sender_email: Optional[EmailStr] = Field(None, description="Gmail address (required if auto_send_emails=true)")
    sender_password: Optional[str] = Field(None, description="Gmail app password (required if auto_send_emails=true)")
    min_delay: int = Field(5, ge=1, le=60, description="Min delay between emails (seconds)")
    max_delay: int = Field(15, ge=1, le=120, description="Max delay between emails (seconds)")


class RunAutomationResponse(BaseModel):
    """Response from automation pipeline"""
    success: bool
    message: str
    stats: dict
    leads: Optional[List[dict]] = None
    error: Optional[str] = None


# ============================================================================
# Error Responses
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str
    error_code: Optional[str] = None


# Update forward references
TokenResponse.model_rebuild()
