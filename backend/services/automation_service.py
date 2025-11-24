"""
Automation Service - Full End-to-End Lead Generation & Outreach Pipeline
This service orchestrates the complete workflow:
1. Scrape leads from source (Google Maps/LinkedIn/Instagram)
2. Generate AI descriptions for each business
3. Generate AI-personalized emails
4. Send emails automatically
"""

import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class AutomationService:
    """
    Complete automation pipeline for lead generation and outreach
    """

    def __init__(self, db, ai_service, email_sender_service):
        self.db = db
        self.ai_service = ai_service
        self.email_sender = email_sender_service

    async def run_full_automation(
        self,
        campaign_id: str,
        tenant_id: str,
        query: str,
        source: str = "google_maps",
        max_results: int = 10,
        generate_descriptions: bool = True,
        generate_emails: bool = True,
        company_info: Optional[str] = None,
        custom_instruction: Optional[str] = None,
        auto_send_emails: bool = False,
        sender_email: Optional[str] = None,
        sender_password: Optional[str] = None,
        min_delay: int = 5,
        max_delay: int = 15,
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """
        Run the complete automation pipeline

        Args:
            campaign_id: Campaign to add leads to
            tenant_id: Tenant ID
            query: Search query
            source: Lead source (google_maps, linkedin, instagram)
            max_results: Max number of leads to collect
            generate_descriptions: Whether to generate AI descriptions
            generate_emails: Whether to generate fully custom AI emails (NO templates!)
            company_info: Your company info - AI uses this to create custom emails
            custom_instruction: Optional custom instructions for email tone/style
            auto_send_emails: Whether to send emails automatically
            sender_email: Gmail address (required if auto_send_emails=True)
            sender_password: Gmail app password (required if auto_send_emails=True)
            min_delay: Min delay between emails (seconds)
            max_delay: Max delay between emails (seconds)
            progress_callback: Callback function for progress updates

        Returns:
            Dict with results and statistics
        """

        def update_progress(step: str, message: str, percentage: int):
            """Helper to send progress updates"""
            if progress_callback:
                progress_callback({
                    "step": step,
                    "message": message,
                    "percentage": percentage
                })

        try:
            stats = {
                "leads_collected": 0,
                "descriptions_generated": 0,
                "emails_generated": 0,
                "emails_sent": 0,
                "emails_failed": 0
            }

            # STEP 1: Scrape Leads
            update_progress("Step 1/4: Scraping Leads", f"Collecting {max_results} leads from {source}...", 10)

            from backend.services.google_maps_scraper import search_places

            # Call the search_places function (it's not async, but that's okay)
            leads_data = search_places(query, max_results=max_results)

            if not leads_data:
                return {
                    "success": False,
                    "message": "No leads found",
                    "error": "No leads found",
                    "stats": stats
                }

            # Save leads to database
            from models.campaign import CampaignLead
            saved_leads = []

            for lead_data in leads_data:
                lead = CampaignLead(
                    id=str(uuid.uuid4()),
                    campaign_id=campaign_id,
                    title=lead_data.get("title", ""),  # Company/Business name
                    address=lead_data.get("address"),
                    phone=lead_data.get("phone"),
                    website=lead_data.get("website"),
                    email=lead_data.get("email"),  # Will be None from scraper (no emails from Google Maps)
                    contact_source=source,  # google_maps, linkedin, etc.
                    scraped_data=lead_data  # Store raw scraper data as JSON
                )
                self.db.add(lead)
                saved_leads.append(lead)

            self.db.commit()
            stats["leads_collected"] = len(saved_leads)

            update_progress("Step 1/4: Leads Collected", f"Successfully collected {len(saved_leads)} leads", 25)

            # STEP 2: Generate AI Descriptions (Optional)
            if generate_descriptions and self.ai_service.is_loaded:
                update_progress("Step 2/4: Generating Descriptions", "Creating AI-powered business descriptions...", 40)

                for i, lead in enumerate(saved_leads):
                    try:
                        # Get category from scraped_data if available
                        category = lead.scraped_data.get("category", "Business") if lead.scraped_data else "Business"

                        description_prompt = f"""
Generate a professional business description for this company:
Company Name: {lead.title}
Category: {category}
Location: {lead.address or 'N/A'}

Write a 2-3 sentence description of what this business likely does and their services.
"""
                        description = self.ai_service.generate_email_content(description_prompt, max_length=150)

                        # Save description to lead
                        lead.description = description
                        stats["descriptions_generated"] += 1

                        if progress_callback and i % 5 == 0:
                            update_progress(
                                "Step 2/4: Generating Descriptions",
                                f"Generated {stats['descriptions_generated']}/{len(saved_leads)} descriptions",
                                40 + int((i / len(saved_leads)) * 15)
                            )
                    except Exception as e:
                        logger.error(f"Failed to generate description for {lead.title}: {e}")

                self.db.commit()
                update_progress("Step 2/4: Descriptions Complete", f"Generated {stats['descriptions_generated']} descriptions", 55)
            else:
                update_progress("Step 2/4: Skipping Descriptions", "Description generation disabled", 55)

            # STEP 3: Generate AI Emails (Optional) - NO TEMPLATES NEEDED!
            if generate_emails and company_info and self.ai_service.is_loaded:
                update_progress("Step 3/4: Generating Emails", "Creating fully customized AI emails...", 60)

                from models.campaign import EmailLog, EmailSendStatus

                for i, lead in enumerate(saved_leads):
                    try:
                        # Extract first name if available (simple extraction)
                        first_name = None
                        if lead.title:
                            # Try to extract first name (before space or comma)
                            name_parts = lead.title.replace(',', ' ').split()
                            if len(name_parts) > 0:
                                first_name = name_parts[0]

                        # Determine greeting
                        greeting = f"Dear {first_name}," if first_name else f"Dear {lead.title} Team,"

                        # Use business description (generated in Step 2) or basic info
                        category = lead.scraped_data.get("category", "Business") if lead.scraped_data else "Business"
                        business_description = lead.description if lead.description else f"{lead.title} - {category} located in {lead.address or 'Unknown location'}"

                        # Generate completely custom email using AI (like Gradio app)
                        email_prompt = f"""
You are an expert business email copywriter.
Your task: Write a professional, customized outreach email to a potential client, introducing your company and inviting them to collaborate or learn more about your services.

**Instructions:**
- Focus on the client's pain points and what makes your company unique.
- Be specific—no empty claims or clichés.
- End with a clear call to action (e.g., request a meeting, a reply, or a demo).
- The email must be ready to send with no placeholders or generic text.
- Maintain a friendly, engaging, and professional tone.
- Generate BOTH the subject line and email body.
- Format output as:
Subject: [Your subject line]

[Email body]

## Your Company Info:
{company_info}

## Recipient Business Description:
{business_description}

## Greeting to use:
{greeting}

Please follow the above instructions carefully and return the complete email with subject line.
"""
                        generated_email = self.ai_service.generate_email_content(email_prompt, max_length=512)

                        # Extract subject and body
                        subject = "Collaboration Opportunity"  # Default
                        body = generated_email

                        if "Subject:" in generated_email:
                            lines = generated_email.split('\n', 2)
                            if len(lines) >= 2:
                                subject = lines[0].replace("Subject:", "").strip()
                                body = lines[1].strip() if len(lines) == 2 else '\n'.join(lines[2:]).strip()

                        # Create email log
                        email_log = EmailLog(
                            id=str(uuid.uuid4()),
                            lead_id=lead.id,
                            campaign_id=campaign_id,
                            template_id=None,  # No template used!
                            tenant_id=tenant_id,
                            recipient_email=lead.email or f"no-email-{lead.id}@placeholder.com",
                            subject=subject,
                            body=body,
                            status=EmailSendStatus.PENDING
                        )
                        self.db.add(email_log)
                        stats["emails_generated"] += 1

                        if progress_callback and i % 3 == 0:
                            update_progress(
                                "Step 3/4: Generating Emails",
                                f"Generated {stats['emails_generated']}/{len(saved_leads)} custom emails",
                                60 + int((i / len(saved_leads)) * 25)
                            )
                    except Exception as e:
                        logger.error(f"Failed to generate email for {lead.title}: {e}")

                self.db.commit()
                update_progress("Step 3/4: Emails Generated", f"Created {stats['emails_generated']} fully customized emails", 85)
            else:
                update_progress("Step 3/4: Skipping Email Generation", "Email generation disabled or missing company info", 85)

            # STEP 4: Send Emails Automatically (Optional)
            if auto_send_emails and sender_email and sender_password and stats["emails_generated"] > 0:
                update_progress("Step 4/4: Sending Emails", "Sending emails via Gmail...", 90)

                # Get pending emails
                from models.campaign import EmailLog, EmailSendStatus
                pending_emails = self.db.query(EmailLog).filter(
                    EmailLog.campaign_id == campaign_id,
                    EmailLog.status == EmailSendStatus.PENDING
                ).all()

                # Send emails
                result = self.email_sender.send_bulk_emails(
                    emails=pending_emails,
                    sender_email=sender_email,
                    sender_password=sender_password,
                    min_delay=min_delay,
                    max_delay=max_delay
                )

                stats["emails_sent"] = result["sent"]
                stats["emails_failed"] = result["failed"]

                self.db.commit()
                update_progress("Step 4/4: Email Sending Complete", f"Sent {stats['emails_sent']} emails", 100)
            else:
                update_progress("Step 4/4: Skipping Email Sending", "Automatic sending disabled", 100)

            return {
                "success": True,
                "message": "Automation pipeline completed successfully!",
                "stats": stats,
                "leads": [{"id": l.id, "name": l.title, "email": l.email} for l in saved_leads]
            }

        except Exception as e:
            logger.error(f"Automation pipeline failed: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Automation pipeline failed: {str(e)}",
                "error": str(e),
                "stats": stats
            }


# Global instance
automation_service = None

def get_automation_service(db, ai_service, email_sender_service):
    """Get or create automation service instance"""
    global automation_service
    if automation_service is None:
        automation_service = AutomationService(db, ai_service, email_sender_service)
    return automation_service
