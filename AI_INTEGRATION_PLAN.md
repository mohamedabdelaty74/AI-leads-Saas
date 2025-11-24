# AI Features Integration Plan

**Date:** 2025-11-12
**Status:** IN PROGRESS
**Completion:** 20% (Database layer done)

---

## Progress Summary

### ✅ COMPLETED (20%)

#### 1. Database Schema for AI Features
**Files Modified:**
- `models/campaign.py` - Added 3 new models ✅
  - `EmailTemplate` - Reusable email templates with AI placeholders
  - `EmailLog` - Track every email sent with status tracking
  - `EmailSendStatus` enum - pending, sent, failed, bounced, opened, clicked, replied

- `models/tenant.py` - Added relationships ✅
  - `email_templates` relationship
  - `email_logs` relationship

**New Database Tables:**
```sql
-- email_templates table
- id, tenant_id, name, description
- subject, body
- is_active, use_ai_personalization
- times_used, created_at, updated_at

-- email_logs table
- id, lead_id, campaign_id, template_id, tenant_id
- recipient_email, subject, body, status
- sent_at, opened_at, clicked_at, replied_at
- error_message, retry_count
- provider_message_id, provider_response
```

---

## 🚧 PENDING WORK (80%)

### Phase 1: Backend Services & APIs (40%)

#### Step 1: Create Database Migration
```bash
cd "E:\first try\AI-leads-Saas-main"
alembic revision --autogenerate -m "Add email templates and logs tables"
alembic upgrade head
```

#### Step 2: Create AI Service Wrapper
**File:** `backend/services/ai_service.py`

**Purpose:** Load Qwen 2.5-7B model once and provide email generation interface

**Key Features:**
- Load model on startup (14GB)
- Generate personalized emails using lead data
- Template variable replacement ({{company_name}}, {{first_name}}, etc.)
- Caching for performance

**API Design:**
```python
class AIService:
    def __init__(self):
        self.model = None  # Qwen/Qwen2.5-7B-Instruct
        self.tokenizer = None

    def load_model(self):
        """Load AI model on startup"""

    def generate_email(
        self,
        template: EmailTemplate,
        lead: CampaignLead,
        company_info: str
    ) -> str:
        """Generate personalized email for lead"""

    def generate_bulk_emails(
        self,
        template: EmailTemplate,
        leads: List[CampaignLead],
        company_info: str
    ) -> List[str]:
        """Generate emails for multiple leads (batch)"""
```

#### Step 3: Create Email Sending Service
**File:** `backend/services/email_sender.py`

**Purpose:** Send emails via Gmail SMTP with rate limiting

**Key Features:**
- Gmail SMTP integration
- Rate limiting (5-15 sec delays between emails)
- Retry logic for failures
- Email log tracking
- Bulk send with progress tracking

**API Design:**
```python
class EmailSenderService:
    def send_email(
        self,
        lead: CampaignLead,
        subject: str,
        body: str,
        sender_email: str,
        app_password: str
    ) -> EmailLog:
        """Send single email and log result"""

    def send_bulk_emails(
        self,
        campaign_id: str,
        sender_email: str,
        app_password: str,
        callback=None  # Progress callback
    ) -> Dict[str, int]:
        """
        Send emails to all leads in campaign
        Returns: {sent: 10, failed: 2, total: 12}
        """
```

#### Step 4: Add Pydantic Schemas
**File:** `backend/schemas.py`

**Add these schemas:**
```python
class EmailTemplateCreate(BaseModel):
    name: str
    description: Optional[str]
    subject: str
    body: str
    use_ai_personalization: bool = True

class EmailTemplateResponse(BaseModel):
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

class GenerateEmailRequest(BaseModel):
    template_id: Optional[str]
    lead_id: str
    custom_template: Optional[str]  # Use custom template instead

class SendEmailRequest(BaseModel):
    lead_ids: List[str]
    template_id: str
    sender_email: str
    sender_password: str  # Gmail app password

class EmailAnalytics(BaseModel):
    total_sent: int
    total_opened: int
    total_clicked: int
    total_replied: int
    open_rate: float
    click_rate: float
    reply_rate: float
```

#### Step 5: Add API Endpoints
**File:** `backend/main.py`

**New Endpoints:**

1. **Email Templates CRUD**
```python
POST   /api/v1/email-templates          # Create template
GET    /api/v1/email-templates          # List templates
GET    /api/v1/email-templates/{id}     # Get template
PUT    /api/v1/email-templates/{id}     # Update template
DELETE /api/v1/email-templates/{id}     # Delete template
```

2. **AI Email Generation**
```python
POST /api/v1/leads/{lead_id}/generate-email
# Generate AI email for single lead
# Body: {template_id: "...", company_info: "..."}
# Response: {email_subject: "...", email_body: "..."}

POST /api/v1/campaigns/{campaign_id}/generate-emails
# Generate AI emails for ALL leads in campaign
# Body: {template_id: "...", company_info: "..."}
# Response: {generated_count: 50, failed_count: 2}
```

3. **Email Sending**
```python
POST /api/v1/leads/{lead_id}/send-email
# Send email to single lead
# Body: {subject: "...", body: "...", sender_email: "...", sender_password: "..."}
# Response: {status: "sent", email_log_id: "..."}

POST /api/v1/campaigns/{campaign_id}/send-emails
# Bulk send emails to all leads with generated_email
# Body: {sender_email: "...", sender_password: "..."}
# Response: {sent: 45, failed: 5, total: 50}
# Returns 202 Accepted (runs in background)

GET /api/v1/campaigns/{campaign_id}/send-emails/status
# Check status of bulk send operation
# Response: {status: "running", progress: 30, total: 50}
```

4. **Email Analytics**
```python
GET /api/v1/campaigns/{campaign_id}/email-analytics
# Get email performance stats
# Response: EmailAnalytics schema

GET /api/v1/email-logs?campaign_id=...&status=sent
# List email logs with filters
# Response: List[EmailLog]
```

---

### Phase 2: Frontend UI Development (40%)

#### Page 1: Email Templates Manager
**Path:** `frontend/src/app/emails/templates/page.tsx`

**Features:**
- List all email templates in table
- Create new template with form
- Edit existing templates
- Delete templates
- Preview template with sample data
- Template variables help: {{company_name}}, {{first_name}}, etc.
- Toggle AI personalization on/off
- View usage stats (times_used)

**UI Components Needed:**
- Template list table
- Create/Edit modal with rich text editor
- Variable inserter dropdown
- Delete confirmation dialog
- Preview panel

#### Page 2: AI Email Composer
**Path:** `frontend/src/app/emails/compose/page.tsx`

**Features:**
- Select campaign
- Select email template
- Enter company information (your business details)
- Click "Generate Emails with AI" button
- Shows progress: "Generating 50 emails..."
- View generated emails in table
- Edit individual emails before sending
- Preview email for each lead
- Regenerate specific emails

**Workflow:**
1. User selects campaign
2. User selects template
3. User enters company info
4. Click "Generate Emails"
5. Backend AI generates personalized email for each lead
6. Frontend shows table of all generated emails
7. User can edit/regenerate before sending

#### Page 3: Email Campaign Manager
**Path:** `frontend/src/app/emails/campaigns/page.tsx`

**Features:**
- Select campaign with generated emails
- Enter Gmail credentials (email + app password)
- Configure sending settings:
  - Delay between emails (5-15 seconds)
  - Daily limit (default 500)
  - Start time, end time
- Click "Start Sending" button
- Real-time progress tracking:
  - "Sending email 25/50..."
  - "Sent: 25, Failed: 2"
- Pause/Resume functionality
- View failed emails with error messages
- Retry failed emails

**Safety Features:**
- Confirm before sending (show total count)
- Show estimated time to complete
- Email preview before sending
- Stop button (cancel operation)
- Rate limiting to avoid Gmail blocks

#### Page 4: Email Analytics Dashboard
**Path:** `frontend/src/app/emails/analytics/page.tsx`

**Features:**
- Campaign selector
- Key metrics cards:
  - Total Sent
  - Open Rate %
  - Click Rate %
  - Reply Rate %
- Email status breakdown (pie chart)
- Timeline graph (emails sent per day)
- Top performing templates
- Recent email activity log
- Export analytics to CSV

**Data Visualization:**
- Charts using recharts or chart.js
- Real-time updates
- Filter by date range
- Compare campaigns

---

## System Requirements

### AI Model Requirements
- **Model:** Qwen/Qwen2.5-7B-Instruct (14GB)
- **GPU:** NVIDIA GPU with 16GB+ VRAM (recommended)
- **CPU:** 16GB RAM minimum for CPU inference (slow)
- **Storage:** 20GB free space for model cache
- **HuggingFace Account:** Required for model access

### Environment Variables Needed
```env
# AI Model
HUGGINGFACE_API_KEY=your_huggingface_token

# Email Sending (per user, not global)
# Users will enter these in UI
# GMAIL_EMAIL=user-enters-in-ui
# GMAIL_APP_PASSWORD=user-enters-in-ui

# Optional: SendGrid for transactional emails
SENDGRID_API_KEY=your_sendgrid_key

# AI Generation Settings
AI_MODEL_NAME=Qwen/Qwen2.5-7B-Instruct
AI_MAX_TOKENS=512
AI_TEMPERATURE=0.9
```

---

## Implementation Roadmap

### Week 1: Backend Foundation (Days 1-3)
- Day 1: Database migration, AI service wrapper
- Day 2: Email sending service with rate limiting
- Day 3: API endpoints for templates, generation, sending

### Week 2: Core Features (Days 4-6)
- Day 4: Email templates UI page
- Day 5: AI email composer UI
- Day 6: Email campaign manager UI

### Week 3: Analytics & Polish (Days 7-9)
- Day 7: Email analytics dashboard
- Day 8: Testing, bug fixes, optimization
- Day 9: Documentation, deployment prep

---

## How Users Will Use The Platform

### Complete User Flow:

**Step 1: Generate Leads** (Already Working ✅)
1. User creates campaign: "Dubai Restaurants"
2. User generates 50 leads from Google Maps
3. Leads saved with: name, address, phone, website, ratings

**Step 2: Create Email Template** (New Feature)
1. User goes to /emails/templates
2. Clicks "New Template"
3. Creates template:
   - Name: "Restaurant Outreach"
   - Subject: "Boost {{company_name}}'s Online Presence"
   - Body: "Hi {{first_name}}, I noticed {{company_name}} has great reviews..."
4. Saves template

**Step 3: Generate AI Emails** (New Feature)
1. User goes to /emails/compose
2. Selects campaign: "Dubai Restaurants"
3. Selects template: "Restaurant Outreach"
4. Enters company info:
   ```
   We're a digital marketing agency specializing in restaurant social media.
   Contact: John Smith
   Email: john@agency.com
   Website: www.agency.com
   ```
5. Clicks "Generate Emails with AI"
6. AI generates 50 personalized emails (takes 2-3 minutes)
7. User reviews generated emails
8. Edits any email that needs tweaking
9. Emails saved to `generated_email` field in database

**Step 4: Send Emails** (New Feature)
1. User goes to /emails/campaigns
2. Selects campaign: "Dubai Restaurants"
3. Enters Gmail credentials:
   - Email: john@agency.com
   - App Password: (from Gmail security settings)
4. Configures:
   - Delay: 10 seconds between emails
   - Daily limit: 500 emails
5. Reviews:
   - "You are about to send 50 emails"
   - Shows estimated time: "~8 minutes"
6. Clicks "Start Sending"
7. Progress bar shows: "Sending 25/50... (Est. 4 min remaining)"
8. Emails sent with delays to avoid spam filters
9. Each email logged to `email_logs` table
10. Failed emails marked with error message
11. Completion: "Sent 48 emails successfully, 2 failed"

**Step 5: Track Performance** (New Feature)
1. User goes to /emails/analytics
2. Views campaign performance:
   - Sent: 48 emails
   - Opened: 32 (66% open rate)
   - Clicked: 15 (31% click rate)
   - Replied: 5 (10% reply rate)
3. Sees which emails performed best
4. Identifies top templates
5. Exports data for reporting

---

## Current Status & Next Steps

### What's Working Now:
✅ Lead generation from Google Maps
✅ Campaign management
✅ Database ready for AI features
✅ Email fields in database (generated_email, email_sent)

### What's Missing:
❌ AI model integration (14GB model not loaded)
❌ Email generation API
❌ Email sending functionality
❌ Email templates UI
❌ Email composer UI
❌ Email campaign manager UI
❌ Email analytics UI

### Immediate Next Steps:
1. **Run database migration** to create new tables
2. **Create AI service** to load Qwen model
3. **Build email generation API** endpoint
4. **Test AI email generation** with sample data
5. **Create simple email sending function** with Gmail
6. **Build basic email templates UI** page

---

## Important Notes

### AI Model Considerations:
- **14GB model is LARGE** - First load takes 5-10 minutes
- **GPU highly recommended** - CPU inference is 10x slower
- **Model stays in memory** - Don't restart server frequently
- **Batch generation** - Generate 50 emails in ~2-3 minutes
- **Quality over speed** - AI emails are personalized and effective

### Email Sending Best Practices:
- **Gmail daily limit:** 500 emails/day for regular accounts, 2000 for Google Workspace
- **Use delays:** 5-15 seconds between emails (configurable)
- **App passwords:** Users must create Gmail app password (not regular password)
- **Avoid spam filters:**
  - Don't send same email to everyone
  - Use AI personalization
  - Include unsubscribe link
  - Valid sender domain
- **Monitor bounces:** Mark bounced emails, don't retry
- **Track opens:** Use tracking pixels (optional)

### Security Considerations:
- **Don't store Gmail passwords** - User enters each time
- **Encrypt sensitive data** - Use environment variables
- **Rate limiting** - Prevent abuse of AI generation
- **Tenant isolation** - Each company's emails are private
- **Email logs** - Audit trail for compliance

---

## Alternative: Quick Start Without AI

If you want email functionality WITHOUT the 14GB AI model, you can:

1. **Use Simple Templates** - Just replace {{variables}} without AI
2. **Manual Email Writing** - User writes each email
3. **Third-party AI APIs** - Use OpenAI GPT-4 API instead of local model
   - Pros: No 14GB download, faster, easier
   - Cons: Costs $0.01-0.03 per email, needs API key, internet required

**OpenAI Alternative:**
```python
# Instead of Qwen model:
import openai

def generate_email_openai(lead, template, company_info):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{
            "role": "user",
            "content": f"Generate email for {lead.title}..."
        }]
    )
    return response.choices[0].message.content
```

---

## Questions to Answer:

1. **Do you want to use the local 14GB AI model or OpenAI API?**
   - Local model: Free, private, requires GPU
   - OpenAI API: Paid (~$0.02/email), fast, no setup

2. **Should I continue building the full integration?**
   - Yes → I'll build all features (2-3 days work)
   - No → I can build a simpler version without AI first

3. **What's your priority?**
   - A. Get basic email sending working first (no AI)
   - B. Get AI email generation working first (no sending yet)
   - C. Build complete end-to-end flow (generation + sending)
   - D. Just show me how to use the existing Gradio app

4. **Do you have a GPU for the AI model?**
   - Yes → We can use local Qwen model
   - No → We should use OpenAI API or cloud GPU

Let me know which direction you want to take!
