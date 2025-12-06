"""
WhatsApp Service - Message Generation and Sending
Handles AI-powered WhatsApp message generation and sending via WhatsApp Cloud API
"""

import os
import logging
import time
import re
import requests
import torch
from typing import Optional, Dict, Tuple
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()


class WhatsAppService:
    """
    WhatsApp Service for generating and sending personalized WhatsApp messages

    Uses the same AI model as email generation for consistency
    Sends via WhatsApp Cloud API (Facebook Graph API)
    """

    def __init__(self, ai_service=None):
        """
        Initialize WhatsApp service

        Args:
            ai_service: Shared AI service instance (to reuse loaded model)
        """
        self.ai_service = ai_service
        self.graph_api_version = "v19.0"
        self.max_message_length = 4096  # WhatsApp limit

    def _normalize_phone(self, phone: str) -> str:
        """
        Normalize phone number to E.164 format
        Keeps leading + if exists, removes spaces, dashes, parentheses

        Args:
            phone: Raw phone number string

        Returns:
            Normalized phone number
        """
        phone = str(phone or "").strip()
        if not phone:
            return ""

        plus_prefix = phone.startswith("+")
        digits = re.sub(r"[^\d]", "", phone)
        return f"+{digits}" if plus_prefix else digits

    def generate_whatsapp_message(
        self,
        lead_name: str,
        lead_description: str,
        company_info: str,
        first_name: Optional[str] = None,
        custom_instruction: Optional[str] = None
    ) -> str:
        """
        Generate personalized WhatsApp message for a single lead using AI

        Args:
            lead_name: Company/person name
            lead_description: Business description
            company_info: Your company information
            first_name: Lead's first name (optional)
            custom_instruction: Additional instructions for AI (optional)

        Returns:
            Generated WhatsApp message (3-6 lines, friendly tone)
        """
        if not self.ai_service or not self.ai_service.is_loaded:
            raise Exception("AI model not loaded. Cannot generate WhatsApp message.")

        try:
            # Base instruction for WhatsApp generation
            base_instruction = f"""
Instructions:
- Craft a short, natural WhatsApp message introducing your service to the company.
- Use friendly, human language (not formal like emails).
- Keep it concise: 3 to 6 lines maximum.
- Use emojis sparingly (1-2 max, only if appropriate).
- End with your name and contact from company info.
- Make it feel personal, not like a template.

## Example 1: (With First Name)
Hi James 👋
I'm [Your Name] from [Your Company].
I noticed your work with SmithTech in AI automation – super impressive!
We specialize in helping SaaS startups like yours gain more visibility through strategic SEO.
Would love to connect for a quick chat if you're open!
– [Your Name] | [Your Company]

## Example 2: (Company Name Only)
Hey Urban Trends Team 👋
I'm [Your Name] from [Your Company].
Loved your focus on sustainable streetwear – it's very on trend 🌱
We help fashion brands grow their audience through social media and targeted ads.
Can we set up a quick call to explore ideas?
– [Your Name] | [Your Company]
"""

            # Combine with custom instruction if provided
            instructions = base_instruction
            if custom_instruction and custom_instruction.strip():
                instructions += f"\n\nAdditional Instructions:\n{custom_instruction.strip()}"

            # Build AI prompt
            messages = [
                {
                    "role": "system",
                    "content": "You are an AI assistant specializing in generating short, effective WhatsApp marketing messages."
                },
                {
                    "role": "user",
                    "content": f"""
🔹 **Our Company Info:**
{company_info}

🔹 **Instructions:**
{instructions}

🔹 **Lead Info:**
Company/Name: {lead_name}
First Name: {first_name or 'N/A'}
Description: {lead_description or 'N/A'}

Please follow the above instructions carefully and return only the WhatsApp message (no extra text, quotes, or formatting).
"""
                }
            ]

            # Generate using AI model
            text_prompt = self.ai_service.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )

            model_inputs = self.ai_service.tokenizer(
                [text_prompt],
                return_tensors="pt"
            ).to(self.ai_service.model.device)

            with torch.no_grad():
                generated_ids = self.ai_service.model.generate(
                    **model_inputs,
                    max_new_tokens=300,
                    do_sample=True,
                    temperature=0.9
                )

            generated_text = self.ai_service.tokenizer.batch_decode(
                generated_ids[:, model_inputs.input_ids.shape[1]:],
                skip_special_tokens=True
            )[0]

            # Clean up and truncate if needed
            message = generated_text.strip()
            if len(message) > self.max_message_length:
                message = message[:self.max_message_length]

            logger.info(f"Generated WhatsApp message for {lead_name}")
            return message

        except Exception as e:
            logger.error(f"Failed to generate WhatsApp message: {e}")
            raise Exception(f"WhatsApp generation failed: {str(e)}")

    def send_whatsapp_message(
        self,
        phone: str,
        message: str,
        phone_number_id: str,
        access_token: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Send WhatsApp message via WhatsApp Cloud API

        Args:
            phone: Recipient phone number (will be normalized to E.164)
            message: Message content to send
            phone_number_id: WhatsApp Business Phone Number ID
            access_token: WhatsApp Business API access token

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            # Normalize phone number
            normalized_phone = self._normalize_phone(phone)
            if not normalized_phone:
                return False, "Invalid phone number"

            # Truncate message if too long
            if len(message) > self.max_message_length:
                message = message[:self.max_message_length]

            # WhatsApp Cloud API endpoint
            url = f"https://graph.facebook.com/{self.graph_api_version}/{phone_number_id}/messages"

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            payload = {
                "messaging_product": "whatsapp",
                "to": normalized_phone,
                "type": "text",
                "text": {"body": message},
            }

            # Send request with retry logic
            session = self._build_session()
            response = session.post(url, headers=headers, json=payload, timeout=15)

            if 200 <= response.status_code < 300:
                logger.info(f"WhatsApp sent successfully to {normalized_phone}")
                return True, None
            else:
                error_msg = self._safe_error_text(response)
                logger.error(f"Failed to send WhatsApp to {normalized_phone}: {error_msg}")
                return False, error_msg

        except requests.RequestException as e:
            logger.error(f"Network error sending WhatsApp: {e}")
            return False, str(e)
        except Exception as e:
            logger.error(f"Unexpected error sending WhatsApp: {e}")
            return False, str(e)

    def verify_credentials(
        self,
        phone_number_id: str,
        access_token: str
    ) -> Tuple[bool, str]:
        """
        Verify WhatsApp Business API credentials

        Args:
            phone_number_id: WhatsApp Business Phone Number ID
            access_token: WhatsApp Business API access token

        Returns:
            Tuple of (is_valid: bool, message: str)
        """
        try:
            url = f"https://graph.facebook.com/{self.graph_api_version}/{phone_number_id}/whatsapp_business_profile"
            headers = {"Authorization": f"Bearer {access_token}"}

            response = requests.get(url, headers=headers, timeout=10)

            if 200 <= response.status_code < 300:
                return True, "WhatsApp credentials verified successfully"
            else:
                error_msg = self._safe_error_text(response)
                return False, f"Invalid credentials: {error_msg}"

        except requests.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            return False, f"Verification error: {str(e)}"

    def _build_session(self, total_retries: int = 3, backoff: float = 0.8) -> requests.Session:
        """
        Build requests session with retry logic for rate limits

        Args:
            total_retries: Number of retries
            backoff: Backoff factor for retries

        Returns:
            Configured requests.Session
        """
        session = requests.Session()
        try:
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry

            retry = Retry(
                total=total_retries,
                backoff_factor=backoff,
                status_forcelist=(429, 500, 502, 503, 504),
                allowed_methods=frozenset(["GET", "POST"]),
                raise_on_status=False,
            )
            adapter = HTTPAdapter(max_retries=retry)
            session.mount("https://", adapter)
            session.mount("http://", adapter)
        except Exception:
            pass  # Continue without retry adapter if unavailable

        return session

    def _safe_error_text(self, response: requests.Response) -> str:
        """
        Safely extract error message from API response

        Args:
            response: requests.Response object

        Returns:
            Error message string
        """
        try:
            json_data = response.json()
            if isinstance(json_data, dict):
                # Graph API returns error.message
                return json_data.get("error", {}).get("message") or str(json_data)
            return str(json_data)
        except Exception:
            return response.text[:500]


# Global instance (initialized with AI service)
whatsapp_service = None

def get_whatsapp_service(ai_service=None):
    """
    Get or create WhatsApp service instance

    Args:
        ai_service: AI service instance to use

    Returns:
        WhatsAppService instance
    """
    global whatsapp_service
    if whatsapp_service is None:
        whatsapp_service = WhatsAppService(ai_service=ai_service)
    elif ai_service and not whatsapp_service.ai_service:
        whatsapp_service.ai_service = ai_service
    return whatsapp_service
