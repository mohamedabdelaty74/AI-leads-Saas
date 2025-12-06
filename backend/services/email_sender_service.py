"""
Email Sender Service - Gmail SMTP Integration
Handles bulk email sending with rate limiting and retry logic
"""

import os
import time
import random
import logging
import smtplib
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Optional, Callable
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class EmailSenderService:
    """
    Email sender service using Gmail SMTP

    Features:
    - Send individual emails
    - Bulk send with rate limiting
    - Automatic retry on failure
    - Email logging for analytics
    - Progress tracking
    """

    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.max_retries = 3
        self.retry_delay = 5  # seconds

    def send_single_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        sender_email: str,
        sender_password: str,
        retry_count: int = 0
    ) -> Dict[str, any]:
        """
        Send a single email via Gmail SMTP

        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            sender_email: Sender Gmail address
            sender_password: Gmail app password (NOT regular password)
            retry_count: Current retry attempt

        Returns:
            Dict with success status and message
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = sender_email
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))

            # Connect and send
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
            server.quit()

            logger.info(f"✅ Email sent successfully to {to_email}")

            return {
                "success": True,
                "recipient": to_email,
                "message": "Email sent successfully"
            }

        except smtplib.SMTPAuthenticationError as e:
            error_msg = "Gmail authentication failed. Please check your email and app password."
            logger.error(f"❌ SMTP Auth Error: {e}")
            return {
                "success": False,
                "recipient": to_email,
                "error": error_msg
            }

        except smtplib.SMTPException as e:
            error_msg = f"SMTP error: {str(e)}"
            logger.error(f"❌ SMTP Error sending to {to_email}: {e}")

            # Retry logic
            if retry_count < self.max_retries:
                logger.info(f"Retrying... (attempt {retry_count + 1}/{self.max_retries})")
                time.sleep(self.retry_delay)
                return self.send_single_email(
                    to_email, subject, body, sender_email, sender_password, retry_count + 1
                )

            return {
                "success": False,
                "recipient": to_email,
                "error": error_msg,
                "retry_count": retry_count
            }

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"❌ Error sending email to {to_email}: {e}")
            return {
                "success": False,
                "recipient": to_email,
                "error": error_msg
            }

    def send_bulk_emails(
        self,
        campaign_id: str,
        sender_email: str,
        sender_password: str,
        db: Session,
        min_delay: int = 5,
        max_delay: int = 15,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, int]:
        """
        Send emails to all leads in a campaign that have generated emails

        Args:
            campaign_id: Campaign ID
            sender_email: Sender Gmail address
            sender_password: Gmail app password
            db: Database session
            min_delay: Minimum delay between emails (seconds)
            max_delay: Maximum delay between emails (seconds)
            progress_callback: Optional callback function(current, total, lead_email)

        Returns:
            Dict with sent/failed/total counts
        """
        from models.campaign import Campaign, CampaignLead, EmailLog, EmailSendStatus

        logger.info(f"Starting bulk email send for campaign {campaign_id}")

        # Get campaign
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        # Get leads with generated emails that haven't been sent
        leads = db.query(CampaignLead).filter(
            CampaignLead.campaign_id == campaign_id,
            CampaignLead.generated_email.isnot(None),
            CampaignLead.email.isnot(None),  # Must have email address
            CampaignLead.email_sent == False
        ).all()

        if not leads:
            logger.warning("No leads found with generated emails ready to send")
            return {"sent": 0, "failed": 0, "total": 0}

        total = len(leads)
        sent_count = 0
        failed_count = 0

        logger.info(f"Found {total} leads ready for email sending")

        for i, lead in enumerate(leads):
            try:
                # Parse generated email (format: "Subject: ...\n\nBody...")
                email_parts = lead.generated_email.split("\n\n", 1)

                if len(email_parts) >= 2:
                    subject = email_parts[0].replace("Subject:", "").strip()
                    body = email_parts[1].strip()
                else:
                    # Fallback if format is different
                    subject = f"Regarding {lead.title}"
                    body = lead.generated_email

                # Send email
                result = self.send_single_email(
                    to_email=lead.email,
                    subject=subject,
                    body=body,
                    sender_email=sender_email,
                    sender_password=sender_password
                )

                # Create email log
                email_log = EmailLog(
                    id=str(uuid.uuid4()),
                    lead_id=lead.id,
                    campaign_id=campaign_id,
                    tenant_id=campaign.tenant_id,
                    recipient_email=lead.email,
                    subject=subject,
                    body=body,
                    status=EmailSendStatus.SENT if result["success"] else EmailSendStatus.FAILED,
                    sent_at=datetime.utcnow() if result["success"] else None,
                    error_message=result.get("error") if not result["success"] else None,
                    retry_count=result.get("retry_count", 0)
                )
                db.add(email_log)

                if result["success"]:
                    # Mark lead as email sent
                    lead.email_sent = True
                    sent_count += 1
                    logger.info(f"✅ [{i+1}/{total}] Sent to {lead.email}")
                else:
                    failed_count += 1
                    logger.error(f"❌ [{i+1}/{total}] Failed to send to {lead.email}: {result.get('error')}")

                # Commit after each email
                db.commit()

                # Progress callback
                if progress_callback:
                    progress_callback(i + 1, total, lead.email, result["success"])

                # Rate limiting - delay between emails to avoid spam filters
                if i < total - 1:  # Don't delay after last email
                    delay = random.uniform(min_delay, max_delay)
                    logger.info(f"⏳ Waiting {delay:.1f} seconds before next email...")
                    time.sleep(delay)

                # Break every 50 emails for a longer pause
                if (i + 1) % 50 == 0 and (i + 1) < total:
                    logger.info(f"🛑 Sent {i+1} emails. Taking a 5-minute break to avoid rate limits...")
                    time.sleep(5 * 60)

            except Exception as e:
                failed_count += 1
                logger.error(f"❌ Error processing lead {lead.id}: {e}")

                # Log the error
                try:
                    email_log = EmailLog(
                        id=str(uuid.uuid4()),
                        lead_id=lead.id,
                        campaign_id=campaign_id,
                        tenant_id=campaign.tenant_id,
                        recipient_email=lead.email or "unknown",
                        subject="",
                        body="",
                        status=EmailSendStatus.FAILED,
                        error_message=str(e)
                    )
                    db.add(email_log)
                    db.commit()
                except:
                    pass

        logger.info(f"✅ Bulk send complete: {sent_count} sent, {failed_count} failed out of {total} total")

        return {
            "sent": sent_count,
            "failed": failed_count,
            "total": total
        }

    def send_to_selected_leads(
        self,
        lead_ids: List[str],
        sender_email: str,
        sender_password: str,
        db: Session,
        min_delay: int = 5,
        max_delay: int = 15
    ) -> Dict[str, int]:
        """
        Send emails to specific selected leads

        Args:
            lead_ids: List of lead IDs to send emails to
            sender_email: Sender Gmail address
            sender_password: Gmail app password
            db: Database session
            min_delay: Minimum delay between emails (seconds)
            max_delay: Maximum delay between emails (seconds)

        Returns:
            Dict with sent/failed/total counts
        """
        from models.campaign import Campaign, CampaignLead, EmailLog, EmailSendStatus

        logger.info(f"Starting email send to {len(lead_ids)} selected leads")

        # Get leads by IDs with generated emails
        leads = db.query(CampaignLead).filter(
            CampaignLead.id.in_(lead_ids),
            CampaignLead.generated_email.isnot(None),
            CampaignLead.email.isnot(None)
        ).all()

        if not leads:
            logger.warning("No valid leads found with generated emails")
            return {"sent": 0, "failed": 0, "total": 0}

        total = len(leads)
        sent_count = 0
        failed_count = 0

        logger.info(f"Found {total} leads ready for email sending")

        for i, lead in enumerate(leads):
            try:
                # Get campaign for tenant_id
                campaign = db.query(Campaign).filter(Campaign.id == lead.campaign_id).first()

                # Parse generated email
                email_parts = lead.generated_email.split("\n\n", 1)

                if len(email_parts) >= 2:
                    subject = email_parts[0].replace("Subject:", "").strip()
                    body = email_parts[1].strip()
                else:
                    subject = f"Regarding {lead.title}"
                    body = lead.generated_email

                # Send email
                result = self.send_single_email(
                    to_email=lead.email,
                    subject=subject,
                    body=body,
                    sender_email=sender_email,
                    sender_password=sender_password
                )

                # Create email log
                email_log = EmailLog(
                    id=str(uuid.uuid4()),
                    lead_id=lead.id,
                    campaign_id=lead.campaign_id,
                    tenant_id=campaign.tenant_id if campaign else None,
                    recipient_email=lead.email,
                    subject=subject,
                    body=body,
                    status=EmailSendStatus.SENT if result["success"] else EmailSendStatus.FAILED,
                    sent_at=datetime.utcnow() if result["success"] else None,
                    error_message=result.get("error") if not result["success"] else None,
                    retry_count=result.get("retry_count", 0)
                )
                db.add(email_log)

                if result["success"]:
                    lead.email_sent = True
                    sent_count += 1
                    logger.info(f"[{i+1}/{total}] Sent to {lead.email}")
                else:
                    failed_count += 1
                    logger.error(f"[{i+1}/{total}] Failed to send to {lead.email}: {result.get('error')}")

                db.commit()

                # Rate limiting
                if i < total - 1:
                    delay = random.uniform(min_delay, max_delay)
                    logger.info(f"Waiting {delay:.1f} seconds before next email...")
                    time.sleep(delay)

            except Exception as e:
                failed_count += 1
                logger.error(f"Error processing lead {lead.id}: {e}")

                try:
                    email_log = EmailLog(
                        id=str(uuid.uuid4()),
                        lead_id=lead.id,
                        campaign_id=lead.campaign_id,
                        tenant_id=campaign.tenant_id if campaign else None,
                        recipient_email=lead.email or "unknown",
                        subject="",
                        body="",
                        status=EmailSendStatus.FAILED,
                        error_message=str(e)
                    )
                    db.add(email_log)
                    db.commit()
                except:
                    pass

        logger.info(f"Email send complete: {sent_count} sent, {failed_count} failed out of {total} total")

        return {
            "sent": sent_count,
            "failed": failed_count,
            "total": total
        }

    def test_connection(self, sender_email: str, sender_password: str) -> Dict[str, any]:
        """
        Test Gmail SMTP connection and authentication

        Args:
            sender_email: Gmail address
            sender_password: Gmail app password

        Returns:
            Dict with success status and message
        """
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            server.quit()

            return {
                "success": True,
                "message": "Gmail connection successful"
            }
        except smtplib.SMTPAuthenticationError:
            return {
                "success": False,
                "error": "Authentication failed. Check your email and app password."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Connection failed: {str(e)}"
            }


# Global instance
email_sender_service = EmailSenderService()


if __name__ == "__main__":
    # Test the email sender
    logging.basicConfig(level=logging.INFO)

    print("Email Sender Service Test")
    print("=" * 60)
    print("Note: You need a Gmail app password to test this")
    print("Get one at: https://myaccount.google.com/apppasswords")
    print("=" * 60)

    # Test connection
    test_email = input("Enter your Gmail address: ")
    test_password = input("Enter your Gmail app password: ")

    result = email_sender_service.test_connection(test_email, test_password)

    if result["success"]:
        print(f"\n✅ {result['message']}")

        # Test sending
        recipient = input("\nEnter recipient email to test: ")
        send_result = email_sender_service.send_single_email(
            to_email=recipient,
            subject="Test Email from AI Leads SaaS",
            body="This is a test email from the AI Leads SaaS platform. If you received this, email sending is working!",
            sender_email=test_email,
            sender_password=test_password
        )

        if send_result["success"]:
            print(f"\n✅ Test email sent successfully to {recipient}")
        else:
            print(f"\n❌ Failed to send test email: {send_result.get('error')}")
    else:
        print(f"\n❌ Connection test failed: {result['error']}")
