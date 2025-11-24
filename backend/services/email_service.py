"""
Email Service using SendGrid
Handles all email notifications for the platform
"""

import os
import logging
from typing import Optional, List
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

logger = logging.getLogger(__name__)

# Email configuration from environment
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
FROM_EMAIL = os.getenv('FROM_EMAIL', 'noreply@yourdomain.com')
SUPPORT_EMAIL = os.getenv('SUPPORT_EMAIL', 'support@yourdomain.com')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')


class EmailServiceError(Exception):
    """Custom exception for email service errors"""
    pass


def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None
) -> bool:
    """
    Send an email using SendGrid

    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML email body
        text_content: Plain text email body (optional)

    Returns:
        True if sent successfully, False otherwise
    """
    # Check if SendGrid is configured
    if not SENDGRID_API_KEY or SENDGRID_API_KEY == 'your-sendgrid-api-key':
        logger.warning(f"SendGrid not configured. Would send email to {to_email}: {subject}")
        logger.info(f"Email content: {html_content[:200]}...")
        return False

    try:
        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )

        if text_content:
            message.plain_text_content = text_content

        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        if response.status_code in [200, 201, 202]:
            logger.info(f"Email sent successfully to {to_email}")
            return True
        else:
            logger.error(f"Failed to send email. Status code: {response.status_code}")
            return False

    except Exception as e:
        logger.error(f"Error sending email to {to_email}: {e}")
        raise EmailServiceError(f"Failed to send email: {str(e)}")


def send_team_invitation(
    to_email: str,
    inviter_name: str,
    company_name: str,
    role: str,
    temp_password: str
) -> bool:
    """
    Send team invitation email

    Args:
        to_email: Invitee email address
        inviter_name: Name of person sending invitation
        company_name: Company/tenant name
        role: Role being assigned (admin/member)
        temp_password: Temporary password for first login

    Returns:
        True if sent successfully
    """
    subject = f"You've been invited to join {company_name}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background-color: #4F46E5;
                color: white;
                padding: 30px;
                text-align: center;
                border-radius: 8px 8px 0 0;
            }}
            .content {{
                background-color: #f9fafb;
                padding: 30px;
                border: 1px solid #e5e7eb;
            }}
            .button {{
                display: inline-block;
                padding: 12px 24px;
                background-color: #4F46E5;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                margin: 20px 0;
            }}
            .credentials {{
                background-color: #fff;
                padding: 15px;
                border-left: 4px solid #4F46E5;
                margin: 20px 0;
            }}
            .footer {{
                text-align: center;
                padding: 20px;
                color: #6b7280;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Welcome to {company_name}!</h1>
            </div>
            <div class="content">
                <p>Hi there,</p>
                <p><strong>{inviter_name}</strong> has invited you to join <strong>{company_name}</strong> on our lead generation platform.</p>

                <p>You've been assigned the role of <strong>{role.title()}</strong>.</p>

                <div class="credentials">
                    <h3>Your Login Credentials:</h3>
                    <p><strong>Email:</strong> {to_email}</p>
                    <p><strong>Temporary Password:</strong> <code>{temp_password}</code></p>
                    <p style="color: #ef4444; font-size: 14px;">⚠️ Please change your password after your first login</p>
                </div>

                <p style="text-align: center;">
                    <a href="{FRONTEND_URL}/login" class="button">Access Your Account</a>
                </p>

                <p>If you have any questions, feel free to reach out to our support team at {SUPPORT_EMAIL}.</p>

                <p>Best regards,<br>The {company_name} Team</p>
            </div>
            <div class="footer">
                <p>This is an automated email. Please do not reply to this message.</p>
                <p>© 2025 {company_name}. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    Welcome to {company_name}!

    {inviter_name} has invited you to join {company_name} on our lead generation platform.

    You've been assigned the role of {role.title()}.

    Your Login Credentials:
    Email: {to_email}
    Temporary Password: {temp_password}

    ⚠️ Please change your password after your first login

    Login at: {FRONTEND_URL}/login

    If you have any questions, contact us at {SUPPORT_EMAIL}.

    Best regards,
    The {company_name} Team
    """

    return send_email(to_email, subject, html_content, text_content)


def send_welcome_email(to_email: str, user_name: str, company_name: str) -> bool:
    """
    Send welcome email to new users

    Args:
        to_email: User email address
        user_name: User's name
        company_name: Company name

    Returns:
        True if sent successfully
    """
    subject = f"Welcome to {company_name} - Let's Get Started!"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px;
                text-align: center;
                border-radius: 8px 8px 0 0;
            }}
            .content {{
                background-color: #fff;
                padding: 30px;
                border: 1px solid #e5e7eb;
            }}
            .feature {{
                padding: 15px;
                margin: 10px 0;
                background-color: #f9fafb;
                border-left: 4px solid #4F46E5;
            }}
            .button {{
                display: inline-block;
                padding: 12px 24px;
                background-color: #4F46E5;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎉 Welcome Aboard, {user_name}!</h1>
                <p>Your lead generation journey starts here</p>
            </div>
            <div class="content">
                <p>Hi {user_name},</p>
                <p>Welcome to {company_name}! We're excited to have you on board.</p>

                <h3>Here's what you can do:</h3>

                <div class="feature">
                    <strong>🗺️ Generate Leads from Google Maps</strong>
                    <p>Search for businesses and extract contact information automatically</p>
                </div>

                <div class="feature">
                    <strong>📧 Create Campaigns</strong>
                    <p>Organize your leads and track your outreach efforts</p>
                </div>

                <div class="feature">
                    <strong>👥 Collaborate with Your Team</strong>
                    <p>Invite team members and work together efficiently</p>
                </div>

                <div class="feature">
                    <strong>📊 Track Performance</strong>
                    <p>Monitor your campaigns with real-time analytics</p>
                </div>

                <p style="text-align: center;">
                    <a href="{FRONTEND_URL}/dashboard" class="button">Go to Dashboard</a>
                </p>

                <p>Need help getting started? Check out our documentation or contact us at {SUPPORT_EMAIL}.</p>

                <p>Happy lead hunting!<br>The {company_name} Team</p>
            </div>
        </div>
    </body>
    </html>
    """

    return send_email(to_email, subject, html_content)


def send_password_reset_email(to_email: str, reset_token: str) -> bool:
    """
    Send password reset email

    Args:
        to_email: User email address
        reset_token: Password reset token

    Returns:
        True if sent successfully
    """
    reset_url = f"{FRONTEND_URL}/reset-password?token={reset_token}"

    subject = "Reset Your Password"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2>Password Reset Request</h2>
            <p>We received a request to reset your password.</p>
            <p>Click the button below to reset your password:</p>
            <p style="text-align: center;">
                <a href="{reset_url}" style="display: inline-block; padding: 12px 24px; background-color: #4F46E5; color: white; text-decoration: none; border-radius: 6px;">
                    Reset Password
                </a>
            </p>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request this, please ignore this email.</p>
            <p>For security, this link can only be used once.</p>
        </div>
    </body>
    </html>
    """

    return send_email(to_email, subject, html_content)


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("Testing Email Service...")
    print("=" * 60)

    # Test sending invitation
    result = send_team_invitation(
        to_email="test@example.com",
        inviter_name="John Doe",
        company_name="Acme Corp",
        role="admin",
        temp_password="TempPass123"
    )

    print(f"Email sent: {result}")
