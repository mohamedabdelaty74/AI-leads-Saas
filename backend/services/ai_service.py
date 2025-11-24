"""
AI Service - Qwen 2.5-7B Model Integration
Handles AI-powered email generation for leads
"""

import os
import logging
import torch
from typing import Optional, List, Dict
from transformers import AutoModelForCausalLM, AutoTokenizer
from huggingface_hub import login
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

class AIService:
    """
    AI Service for generating personalized emails using Qwen 2.5-7B model

    The model is loaded once on startup and kept in memory for fast generation.
    Model size: 14GB (requires 16GB GPU VRAM or 32GB RAM for CPU)
    """

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.model_id = os.getenv("AI_MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct")
        self.is_loaded = False

    def load_model(self):
        if self.is_loaded:
            logger.info("AI model already loaded")
            return

        try:
            model_path = os.getenv("AI_MODEL_PATH", self.model_id)  # ← استخدم المسار المحلي إن وُجد

            logger.info(f"Loading AI model from: {model_path}")

            # Login to HuggingFace if API key provided (still optional)
            hf_token = os.getenv("HUGGINGFACE_API_KEY")
            if hf_token:
                login(token=hf_token)
                logger.info("Logged in to HuggingFace")

            os.environ["CUDA_LAUNCH_BLOCKING"] = "1"
            os.environ["TORCH_USE_CUDA_DSA"] = "1"

            logger.info("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True
            )

            logger.info("Loading model (from local path or cache)...")
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                trust_remote_code=True,
                torch_dtype=torch.bfloat16,
                device_map="auto"
            )

            self.is_loaded = True
            device = "GPU" if torch.cuda.is_available() else "CPU"
            logger.info(f"✅ AI model loaded successfully on {device}!")

        except Exception as e:
            logger.error(f"Failed to load AI model: {e}")
            self.is_loaded = False
            raise Exception(f"AI model loading failed: {str(e)}")
    def generate_email(
        self,
        lead_name: str,
        lead_title: str,
        lead_description: str,
        template_subject: str,
        template_body: str,
        company_info: str,
        first_name: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate personalized email for a single lead

        Args:
            lead_name: Company/person name
            lead_title: Lead title from scraping
            lead_description: Business description (from Google Maps)
            template_subject: Email subject template with {{variables}}
            template_body: Email body template with {{variables}}
            company_info: Your company information
            first_name: Lead's first name (optional)

        Returns:
            Dict with 'subject' and 'body' keys containing generated email
        """
        if not self.is_loaded:
            raise Exception("AI model not loaded. Call load_model() first.")

        try:
            # Prepare greeting
            greeting = f"Dear {first_name}," if first_name else f"Dear {lead_title} Team,"

            # Build prompt for AI
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert business email copywriter specializing in B2B outreach."
                },
                {
                    "role": "user",
                    "content": f"""
Generate a professional, personalized cold outreach email.

📌 OUR COMPANY INFO:
{company_info}

📌 LEAD INFO:
Company: {lead_title}
Description: {lead_description or "N/A"}

📌 TEMPLATE TO FOLLOW:
Subject: {template_subject}
Body: {template_body}

📌 INSTRUCTIONS:
- Replace {{{{company_name}}}} with {lead_title}
- Replace {{{{first_name}}}} with {first_name or lead_title}
- Replace {{{{your_company}}}} with your company name from company info
- Use the greeting: {greeting}
- Make it personalized based on their business description
- Keep it concise (max 150 words)
- Include clear call-to-action
- Be professional but friendly
- NO generic phrases or clichés
- Must feel like it was written specifically for {lead_title}

Return ONLY the email subject and body, no extra text.
Format:
Subject: [generated subject]

[generated email body]
"""
                }
            ]

            # Apply chat template
            text_prompt = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )

            # Tokenize
            model_inputs = self.tokenizer(
                [text_prompt],
                return_tensors="pt"
            ).to(self.model.device)

            # Generate
            logger.info(f"Generating email for {lead_title}...")
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **model_inputs,
                    max_new_tokens=512,
                    do_sample=True,
                    temperature=0.9,
                    top_p=0.95
                )

            # Decode
            generated_text = self.tokenizer.batch_decode(
                generated_ids[:, model_inputs.input_ids.shape[1]:],
                skip_special_tokens=True
            )[0]

            # Parse subject and body
            email_parts = generated_text.strip().split("\n\n", 1)

            if len(email_parts) >= 2:
                subject_line = email_parts[0].replace("Subject:", "").strip()
                body_text = email_parts[1].strip()
            else:
                # Fallback if parsing fails
                subject_line = template_subject.replace("{{company_name}}", lead_title)
                body_text = generated_text.strip()

            logger.info(f"✅ Generated email for {lead_title}")

            return {
                "subject": subject_line,
                "body": body_text
            }

        except Exception as e:
            logger.error(f"Error generating email for {lead_title}: {e}")
            # Return template with simple variable replacement as fallback
            return {
                "subject": template_subject.replace("{{company_name}}", lead_title),
                "body": template_body.replace("{{company_name}}", lead_title).replace("{{first_name}}", first_name or lead_title)
            }

    def generate_email_content(self, prompt: str, max_length: int = 512) -> str:
        """
        Generate text content from a prompt using AI

        Args:
            prompt: The prompt to generate content from
            max_length: Maximum tokens to generate (default 512)

        Returns:
            Generated text content
        """
        if not self.is_loaded:
            raise Exception("AI model not loaded. Call load_model() first.")

        try:
            # Build messages for chat model
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant that generates professional business content."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            # Apply chat template
            text_prompt = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )

            # Tokenize
            model_inputs = self.tokenizer(
                [text_prompt],
                return_tensors="pt"
            ).to(self.model.device)

            # Generate
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **model_inputs,
                    max_new_tokens=max_length,
                    do_sample=True,
                    temperature=0.8,
                    top_p=0.95
                )

            # Decode
            generated_text = self.tokenizer.batch_decode(
                generated_ids[:, model_inputs.input_ids.shape[1]:],
                skip_special_tokens=True
            )[0]

            return generated_text.strip()

        except Exception as e:
            logger.error(f"Error generating content: {e}")
            raise Exception(f"Content generation failed: {str(e)}")

    def generate_bulk_emails(
        self,
        leads: List[Dict],
        template_subject: str,
        template_body: str,
        company_info: str,
        progress_callback=None
    ) -> List[Dict[str, str]]:
        """
        Generate emails for multiple leads in batch

        Args:
            leads: List of lead dicts with 'title', 'description', etc.
            template_subject: Email subject template
            template_body: Email body template
            company_info: Your company information
            progress_callback: Optional callback function(current, total)

        Returns:
            List of dicts with 'subject' and 'body' for each lead
        """
        if not self.is_loaded:
            raise Exception("AI model not loaded. Call load_model() first.")

        results = []
        total = len(leads)

        logger.info(f"Generating emails for {total} leads...")

        for i, lead in enumerate(leads):
            try:
                email = self.generate_email(
                    lead_name=lead.get("title", ""),
                    lead_title=lead.get("title", ""),
                    lead_description=lead.get("description", ""),
                    template_subject=template_subject,
                    template_body=template_body,
                    company_info=company_info,
                    first_name=lead.get("first_name")
                )

                results.append({
                    "lead_id": lead.get("id"),
                    "subject": email["subject"],
                    "body": email["body"],
                    "success": True
                })

                # Call progress callback
                if progress_callback:
                    progress_callback(i + 1, total)

                logger.info(f"Progress: {i+1}/{total} emails generated")

            except Exception as e:
                logger.error(f"Failed to generate email for lead {lead.get('title')}: {e}")
                results.append({
                    "lead_id": lead.get("id"),
                    "subject": template_subject,
                    "body": template_body,
                    "success": False,
                    "error": str(e)
                })

        logger.info(f"✅ Bulk generation complete: {total} emails")
        return results

    def generate_business_research(
        self,
        company_name: str,
        company_data: str = ""
    ) -> str:
        """
        Generate detailed business research and intelligence for a company

        Args:
            company_name: Name of the company
            company_data: Additional data about the company (optional)

        Returns:
            Structured business intelligence report
        """
        if not self.is_loaded:
            raise Exception("AI model not loaded. Call load_model() first.")

        # Create the research prompt
        messages = [
            {
                "role": "system",
                "content": "You are a business intelligence researcher providing structured company analysis for B2B sales and marketing professionals."
            },
            {
                "role": "user",
                "content": f"""Analyze {company_name} and provide a comprehensive business intelligence report in this exact format:

**Business:** [Describe their core business in 1 clear sentence]

**Industry Position:** [Market position, company size, and reputation in 1-2 sentences]

**Key Strengths:** [List 2-3 main competitive advantages or unique selling points]

**Growth Indicators:** [Revenue trends, expansion plans, awards, partnerships, or recent achievements]

**Challenges/Pain Points:** [1-2 main business challenges they likely face that present sales opportunities]

**Decision Makers:** [Likely titles of key decision makers (e.g., CEO, Marketing Director, Operations Manager)]

**Best Approach:** [One sentence on how to effectively approach them for B2B services]

Additional context: {company_data if company_data else "No additional data provided - use general business knowledge"}

Keep each section concise but actionable. Total response under 250 words. Focus on insights useful for B2B sales outreach."""
            }
        ]

        try:
            # Apply chat template
            text_prompt = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )

            # Tokenize
            model_inputs = self.tokenizer(
                [text_prompt],
                return_tensors="pt"
            ).to(self.model.device)

            # Generate with research-optimized parameters
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **model_inputs,
                    max_new_tokens=400,
                    temperature=0.7,
                    do_sample=True,
                    top_p=0.9,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )

            # Decode
            generated_text = self.tokenizer.batch_decode(
                generated_ids[:, model_inputs.input_ids.shape[1]:],
                skip_special_tokens=True
            )[0]

            # Clean and format the response
            research_report = generated_text.strip()

            # Extract structured content if present
            if "**Business:**" in research_report:
                start_idx = research_report.find("**Business:**")
                research_report = research_report[start_idx:].strip()

            logger.info(f"Generated business research for {company_name}")
            return research_report

        except Exception as e:
            logger.error(f"Error generating business research: {e}")
            return f"**Business:** {company_name}\n\n**Note:** Detailed research unavailable at this time. {str(e)}"

    def analyze_csv_columns(
        self,
        headers: List[str],
        sample_rows: List[Dict],
        required_fields: List[str] = None,
        optional_fields: List[str] = None
    ) -> Dict:
        """
        Intelligently analyze CSV columns and map them to database fields

        Args:
            headers: List of CSV column names
            sample_rows: Sample data rows (2-3 rows) for context
            required_fields: Must-have fields (default: ['name'])
            optional_fields: Nice-to-have fields (default: ['email', 'phone', etc.])

        Returns:
            Dict with:
            - field_mapping: Dict mapping our fields to CSV columns
            - additional_context_fields: List of other useful columns for email personalization
            - confidence_scores: Dict of confidence scores for each mapping
        """
        if not self.is_loaded:
            raise Exception("AI model not loaded. Call load_model() first.")

        if required_fields is None:
            required_fields = ['name']
        if optional_fields is None:
            optional_fields = ['email', 'phone', 'address', 'website', 'description', 'generated_email']

        try:
            # Create prompt for AI to analyze columns
            messages = [
                {
                    "role": "system",
                    "content": "You are a data mapping expert specializing in business lead data analysis. Analyze CSV columns and intelligently map them to database fields. Also identify additional columns useful for email personalization."
                },
                {
                    "role": "user",
                    "content": f"""Analyze these CSV columns and map them to our CRM database fields.

**CSV Columns:**
{', '.join(headers)}

**Sample Data (first 2 rows):**
{sample_rows}

**Database Fields to Map:**

REQUIRED:
- name: Company/business/organization name

OPTIONAL:
- email: Email address or contact email
- phone: Phone number or telephone
- address: Physical address, location, or city
- website: Website URL or domain
- description: Business description, overview, background, or "about" text
- generated_email: Pre-written email content, pitch, or outreach message

**Instructions:**
1. Map each database field to the MOST RELEVANT CSV column
2. Identify ALL other columns that would be useful for personalizing sales emails (e.g., industry, revenue, employee count, rating, reviews, services, etc.)
3. Return ONLY valid JSON in this exact format:

{{
  "field_mapping": {{
    "name": "CSV_Column_Name_Here",
    "email": "CSV_Column_Name_Here or null",
    "phone": "CSV_Column_Name_Here or null",
    "address": "CSV_Column_Name_Here or null",
    "website": "CSV_Column_Name_Here or null",
    "description": "CSV_Column_Name_Here or null",
    "generated_email": "CSV_Column_Name_Here or null"
  }},
  "additional_context_fields": [
    "Industry",
    "Rating",
    "Reviews",
    "Category"
  ],
  "confidence": {{
    "name": 0.95,
    "email": 0.80
  }}
}}

Rules:
- Only include CSV column names that ACTUALLY EXIST in the headers list
- Use null for fields that cannot be mapped
- Confidence: 0.0-1.0 (only include if >0.5)
- Additional context fields: columns useful for sales personalization
- Return ONLY the JSON, no markdown, no explanation
"""
                }
            ]

            # Apply chat template
            text_prompt = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )

            # Tokenize
            model_inputs = self.tokenizer(
                [text_prompt],
                return_tensors="pt"
            ).to(self.model.device)

            # Generate
            logger.info("Analyzing CSV columns with AI...")
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **model_inputs,
                    max_new_tokens=512,
                    temperature=0.3,  # Lower temperature for more deterministic output
                    do_sample=True,
                    top_p=0.9,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )

            # Decode
            generated_text = self.tokenizer.batch_decode(
                generated_ids[:, model_inputs.input_ids.shape[1]:],
                skip_special_tokens=True
            )[0]

            # Parse JSON response
            import json
            import re

            # Extract JSON from response (in case AI adds extra text)
            json_match = re.search(r'\{[\s\S]*\}', generated_text)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)
            else:
                # Fallback: return empty mapping
                logger.warning("Could not parse AI response as JSON, using empty mapping")
                result = {
                    "field_mapping": {},
                    "additional_context_fields": [],
                    "confidence": {}
                }

            logger.info(f"AI column mapping complete: {result}")
            return result

        except Exception as e:
            logger.error(f"Error analyzing CSV columns: {e}")
            # Return empty mapping on error
            return {
                "field_mapping": {},
                "additional_context_fields": [],
                "confidence": {},
                "error": str(e)
            }

    def unload_model(self):
        """
        Unload model from memory to free up resources
        Use this if you need to free 14GB of memory
        """
        if self.model:
            del self.model
            del self.tokenizer
            torch.cuda.empty_cache()
            self.is_loaded = False
            logger.info("AI model unloaded from memory")


# Global AI service instance (singleton)
ai_service = AIService()


# Initialize model on module import (optional - can be done on first request instead)
def initialize_ai():
    """Initialize AI model on startup"""
    try:
        logger.info("Initializing AI service...")
        ai_service.load_model()
        return True
    except Exception as e:
        logger.error(f"Failed to initialize AI: {e}")
        logger.warning("AI features will be disabled")
        return False


if __name__ == "__main__":
    # Test the AI service
    logging.basicConfig(level=logging.INFO)

    print("Testing AI Service...")
    print("=" * 60)

    # Load model
    ai_service.load_model()

    # Test email generation
    test_email = ai_service.generate_email(
        lead_name="Bombay Borough",
        lead_title="Bombay Borough",
        lead_description="Fine Indian restaurant in Dubai with 4.8★ rating (8,499 reviews)",
        template_subject="Boost {{company_name}}'s Social Media Presence",
        template_body="Hi {{first_name}}, we noticed {{company_name}} has amazing reviews...",
        company_info="We're a digital marketing agency specializing in restaurant social media. Contact: John Smith, Email: john@agency.com",
        first_name="Manager"
    )

    print("\n✅ Generated Email:")
    print(f"Subject: {test_email['subject']}")
    print(f"\n{test_email['body']}")
