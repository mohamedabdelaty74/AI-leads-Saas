import os
import time
import sqlite3
import requests
import pandas as pd
from serpapi import GoogleSearch
from transformers import pipeline
from huggingface_hub import login
from dotenv import load_dotenv

# ================== UPGRADED APPROACH WITH CACHING ==================
load_dotenv()
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
HF_TOKEN = os.getenv("HUGGINGFACE_API_KEY")

login(token=HF_TOKEN)

# Import model manager to get shared models from Gradio
try:
    from gen.model_manager import get_qwen_model, get_qwen_tokenizer, get_bart_summarizer, models_available
except ImportError:
    # Fallback if model_manager not available
    def get_qwen_model(): return None
    def get_qwen_tokenizer(): return None
    def get_bart_summarizer(): return None
    def models_available(): return {"qwen": False, "tokenizer": False, "bart": False}

# Get shared models (loaded once in gradio_saas_integrated.py)
# This prevents loading 56GB total (4x 14GB) and connection timeouts
def get_research_model():
    """Get shared Qwen research model"""
    return get_qwen_model()

def get_research_tokenizer():
    """Get shared Qwen tokenizer"""
    return get_qwen_tokenizer()

def get_summarizer():
    """Get shared BART summarizer"""
    return get_bart_summarizer()

print("[INFO] Using shared model manager - models loaded in main app only")

# SQLite cache for performance and cost savings
CACHE_DB = "description_cache.db"

def get_cache_connection():
    """Get a thread-safe database connection"""
    conn = sqlite3.connect(CACHE_DB, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_cache_db():
    """Initialize the cache database"""
    conn = get_cache_connection()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS cache (
        company TEXT PRIMARY KEY,
        description TEXT,
        score INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

# Initialize cache database
init_cache_db()

def calculate_lead_score(text):
    """Enhanced lead scoring with growth and award indicators"""
    score = 50
    text = text.lower()

    # Company size indicators
    if any(term in text for term in ['fortune 500', 'public company', 'nasdaq', 'nyse']):
        score += 30
    elif any(term in text for term in ['enterprise', 'corporation', 'inc.', 'ltd.']):
        score += 20
    elif any(term in text for term in ['startup', 'small business', 'founded']):
        score += 10

    # Industry relevance
    high_value = ['technology', 'software', 'healthcare', 'finance', 'consulting']
    medium_value = ['retail', 'education', 'manufacturing']

    if any(ind in text for ind in high_value):
        score += 15
    elif any(ind in text for ind in medium_value):
        score += 5

    # Growth indicators (NEW!)
    if "expanding" in text or "growing" in text:
        score += 10
    if "award" in text or "recognized" in text:
        score += 10

    # Contact quality indicators
    if 'contact' in text or 'email' in text:
        score += 10
    if 'phone' in text or 'call' in text:
        score += 5
    if 'linkedin' in text:
        score += 5

    # Negative indicators
    if any(term in text for term in ['closed', 'bankruptcy', 'out of business']):
        score -= 20
    elif any(term in text for term in ['reviews', 'complaints', 'poor service']):
        score -= 5

    return min(score, 100)

def summarize_text(company_name, text, style="professional"):
    """Generate description with style control"""
    summarizer = get_summarizer()

    # If BART summarizer not available, use simple text extraction
    if summarizer is None:
        # Simple fallback: extract first 100 words
        words = text.split()[:100]
        return " ".join(words) + "..."

    style_prompts = {
        "professional": f"Write a professional company description for {company_name} under 100 words:\n{text}",
        "sales": f"Write a sales-focused pitch for {company_name}, highlighting why a client should work with them:\n{text}",
        "casual": f"Describe {company_name} in a friendly and simple way under 80 words:\n{text}"
    }
    chosen = style_prompts.get(style, style_prompts["professional"])
    summary = summarizer(chosen, max_length=120, min_length=40, do_sample=False)[0]["summary_text"]
    return summary.strip()

def generate_research_summary(company_name, text):
    """Generate deep research insights in concise format"""
    import torch

    research_model = get_research_model()
    research_tokenizer = get_research_tokenizer()

    if research_model is None or research_tokenizer is None:
        return "Research mode unavailable (Qwen model not loaded)"

    prompt = f"""You are a business intelligence researcher. Based on the data about {company_name}, provide a concise but comprehensive research summary in exactly this format:

**Business:** [Core business in 1 sentence]
**Industry Position:** [Market position, size, reputation in 1 sentence]
**Key Strengths:** [2-3 main competitive advantages]
**Growth Indicators:** [Revenue growth, expansion, awards, partnerships]
**Challenges/Pain Points:** [1-2 main business challenges they likely face]
**Decision Makers:** [Likely titles of key contacts]
**Best Approach:** [How to approach them for services - 1 sentence]

Keep each section concise but insightful. Total response should be under 200 words but contain actionable intelligence.

Data:
{text}"""

    messages = [
        {"role": "system", "content": "You are a business intelligence researcher providing concise company analysis."},
        {"role": "user", "content": prompt}
    ]

    text_prompt = research_tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    model_inputs = research_tokenizer([text_prompt], return_tensors="pt").to(research_model.device)

    with torch.no_grad():
        generated_ids = research_model.generate(
            **model_inputs,
            max_new_tokens=250,
            do_sample=True,
            temperature=0.6
        )

    generated_text = research_tokenizer.batch_decode(
        generated_ids[:, model_inputs.input_ids.shape[1]:],
        skip_special_tokens=True
    )[0]

    return generated_text.strip()

def research_summary(company_name, text, style="professional"):
    """Generate deep research insights in concise format with style options"""
    import torch

    research_model = get_research_model()
    research_tokenizer = get_research_tokenizer()

    if research_model is None or research_tokenizer is None:
        return f"Research summary mode unavailable (research model not loaded)."

    # Style-specific prompts for research mode
    style_instructions = {
        "professional": "Use formal business language and focus on strategic insights.",
        "sales": "Emphasize sales opportunities, pain points, and how to position services effectively.",
        "casual": "Use friendly, easy-to-understand language while maintaining business insights."
    }

    style_instruction = style_instructions.get(style, style_instructions["professional"])

    prompt = f"""
You are a business intelligence researcher. Based on the data about {company_name}, provide a concise but comprehensive research summary in exactly this format. {style_instruction}

**Business:** [Core business in 1 sentence]
**Industry Position:** [Market position, size, reputation in 1 sentence]
**Key Strengths:** [2-3 main competitive advantages]
**Growth Indicators:** [Revenue growth, expansion, awards, partnerships]
**Challenges/Pain Points:** [1-2 main business challenges they likely face]
**Decision Makers:** [Likely titles of key contacts]
**Best Approach:** [How to approach them for services - 1 sentence]

Keep each section concise but insightful. Total response should be under 200 words but contain actionable intelligence.

Data:
{text}
"""

    messages = [
        {"role": "system", "content": "You are a business intelligence researcher providing structured company analysis."},
        {"role": "user", "content": prompt}
    ]

    text_prompt = research_tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    model_inputs = research_tokenizer([text_prompt], return_tensors="pt").to(research_model.device)

    with torch.no_grad():
        generated_ids = research_model.generate(
            **model_inputs,
            max_new_tokens=300,
            temperature=0.6,
            do_sample=True,
            pad_token_id=research_tokenizer.eos_token_id,
            eos_token_id=research_tokenizer.eos_token_id
        )

    generated_text = research_tokenizer.batch_decode(
        generated_ids[:, model_inputs.input_ids.shape[1]:],
        skip_special_tokens=True
    )[0]

    # Clean the AI response to extract only the structured business intelligence
    cleaned_text = generated_text.strip()

    # If the response contains the structured format, extract it
    if "**Business:**" in cleaned_text:
        start_idx = cleaned_text.find("**Business:**")
        cleaned_text = cleaned_text[start_idx:].strip()

    return cleaned_text

def analyze_business(company_name, text):
    """Generate full consulting analysis - copied from generate_descriptiongpt.py"""
    if not RESEARCH_AVAILABLE:
        return f"Consulting analysis mode unavailable (research model not loaded)."

    prompt = f"""
You are a business and marketing consultant.
Based on the data below about {company_name}, write a structured report including:

1. Business Identity
2. Strengths
3. Challenges and Opportunities
4. Entry Points for Marketing/Consulting Services
5. Suggested Pitching Approach

The answer must be ONE continuous body of text with clear headings, professional tone, and easy to read.
Avoid tables.

Data:
{text}
"""

    messages = [
        {"role": "system", "content": "You are a business and marketing consultant providing detailed company analysis."},
        {"role": "user", "content": prompt}
    ]

    text_prompt = research_tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    model_inputs = research_tokenizer([text_prompt], return_tensors="pt").to(research_model.device)

    with torch.no_grad():
        generated_ids = research_model.generate(
            **model_inputs,
            max_new_tokens=600,
            temperature=0.7,
            do_sample=True,
            pad_token_id=research_tokenizer.eos_token_id,
            eos_token_id=research_tokenizer.eos_token_id
        )

    generated_text = research_tokenizer.batch_decode(
        generated_ids[:, model_inputs.input_ids.shape[1]:],
        skip_special_tokens=True
    )[0]

    return generated_text.strip()

def smart_company_description(company_name, max_results=8, style="professional", mode="summary", use_cache=True):
    """UPGRADED: Fast, cached, style-controlled company descriptions with research modes"""
    # Check cache first
    if use_cache:
        conn = get_cache_connection()
        c = conn.cursor()
        c.execute("SELECT description, score FROM cache WHERE company=?", (company_name,))
        cached = c.fetchone()
        conn.close()

        if cached:
            print(f"[CACHE] Cache hit for {company_name}")
            return cached[0]  # Return just description for backward compatibility

    # Search for company info with better filtering
    params = {
        "engine": "google",
        "q": f'"{company_name}" company profile',  # More specific search
        "api_key": SERPAPI_KEY,
        "num": max_results
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    organic_results = results.get("organic_results", [])

    # Filter search results to avoid mixing different companies
    filtered_results = []
    company_keywords = company_name.lower().split()

    for item in organic_results:
        title = item.get('title', '').lower()
        snippet = item.get('snippet', '').lower()

        # Check if this result is relevant to the company we're looking for
        is_relevant = False
        for keyword in company_keywords:
            if keyword in title or keyword in snippet:
                is_relevant = True
                break

        # Only include relevant results
        if is_relevant:
            filtered_results.append(f"{item.get('title','')} {item.get('snippet','')}")

    # Use filtered results, fallback to all results if no good matches
    combined_text = " ".join(filtered_results) if filtered_results else " ".join([f"{item.get('title','')} {item.get('snippet','')}" for item in organic_results])

    if not combined_text.strip():
        return company_name

    try:
        # Generate description based on mode - copied logic from generate_descriptiongpt.py
        if mode == "research":
            description = research_summary(company_name, combined_text, style)
        elif mode == "analysis":
            description = analyze_business(company_name, combined_text)
        else:  # summary mode (default)
            description = summarize_text(company_name, combined_text, style)

        score = calculate_lead_score(combined_text)

        # Cache the result with new connection (only cache summary mode for consistency)
        if use_cache and mode == "summary":
            conn = get_cache_connection()
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO cache (company, description, score) VALUES (?, ?, ?)",
                      (company_name, description, score))
            conn.commit()
            conn.close()

        print(f"[GENERATED] Fresh {mode} description for {company_name} (Score: {score}/100)")
        return description

    except Exception as e:
        print(f"[❌ Error generating description]: {e}")
        return combined_text[:300] if combined_text.strip() else company_name

def smart_company_description_with_score(company_name, max_results=8, style="professional", mode="summary", use_cache=True):
    """UPGRADED: Get company description AND lead score with caching"""
    # Check cache first
    if use_cache:
        conn = get_cache_connection()
        c = conn.cursor()
        c.execute("SELECT description, score FROM cache WHERE company=?", (company_name,))
        cached = c.fetchone()
        conn.close()

        if cached:
            print(f"[CACHE] Cache hit for {company_name}")
            return cached[0], cached[1]

    # Search for company info with better filtering (same as generate_descriptiongpt.py logic)
    params = {
        "engine": "google",
        "q": f'"{company_name}" company profile',  # More specific search
        "api_key": SERPAPI_KEY,
        "num": max_results
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    organic_results = results.get("organic_results", [])

    # Filter search results to avoid mixing different companies (same filtering logic)
    filtered_results = []
    company_keywords = company_name.lower().split()

    for item in organic_results:
        title = item.get('title', '').lower()
        snippet = item.get('snippet', '').lower()

        # Check if this result is relevant to the company we're looking for
        is_relevant = False
        for keyword in company_keywords:
            if keyword in title or keyword in snippet:
                is_relevant = True
                break

        # Only include relevant results
        if is_relevant:
            filtered_results.append(f"{item.get('title','')} {item.get('snippet','')}")

    # Use filtered results, fallback to all results if no good matches
    combined_text = " ".join(filtered_results) if filtered_results else " ".join([f"{item.get('title','')} {item.get('snippet','')}" for item in organic_results])

    if not combined_text.strip():
        return company_name, 0

    try:
        # Generate description based on mode - copied logic from generate_descriptiongpt.py
        if mode == "research":
            description = research_summary(company_name, combined_text, style)
        elif mode == "analysis":
            description = analyze_business(company_name, combined_text)
        else:  # summary mode (default)
            description = summarize_text(company_name, combined_text, style)

        score = calculate_lead_score(combined_text)

        # Cache the result with new connection (only cache summary mode for consistency)
        if use_cache and mode == "summary":
            conn = get_cache_connection()
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO cache (company, description, score) VALUES (?, ?, ?)",
                      (company_name, description, score))
            conn.commit()
            conn.close()

        print(f"[GENERATED] Fresh {mode} description for {company_name} (Score: {score}/100)")
        return description, score

    except Exception as e:
        print(f"[❌ Error generating description]: {e}")
        return (combined_text[:300] if combined_text.strip() else company_name), 0

def smart_company_research(company_name, max_results=8, use_cache=False):
    """NEW: Generate deep research insights for a company"""
    # Search for company info (more results for research)
    params = {
        "engine": "google",
        "q": company_name,
        "api_key": SERPAPI_KEY,
        "num": max_results
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    organic_results = results.get("organic_results", [])

    combined_text = " ".join([f"{item.get('title','')} {item.get('snippet','')}" for item in organic_results])

    if not combined_text.strip():
        return f"No research data found for {company_name}", 0

    try:
        # Generate research summary
        research_summary = generate_research_summary(company_name, combined_text)
        score = calculate_lead_score(combined_text)

        print(f"[RESEARCH] Generated research summary for {company_name} (Score: {score}/100)")
        return research_summary, score

    except Exception as e:
        print(f"[❌ Error generating research]: {e}")
        return f"Research unavailable for {company_name}: {e}", 0

def get_business_info_for_emailing(input_file, output_file):
    file_ext = os.path.splitext(input_file)[-1].lower()
    if file_ext == ".csv":
        df = pd.read_csv(input_file)
    elif file_ext in [".xls", ".xlsx"]:
        df = pd.read_excel(input_file, engine='openpyxl')
    else:
        print("Unsupported file format! Please provide a CSV or Excel file.")
        return

    # ✅ FLEXIBLE COLUMN DETECTION - Support both "Title" and "company_name"
    possible_title_columns = ['Title', 'title', 'Company', 'company', 'Company Name', 'company_name',
                             'CompanyName', 'Business', 'business', 'Name', 'name', 'Business Name', 'business_name']

    title_column = None
    for col in possible_title_columns:
        if col in df.columns:
            title_column = col
            break

    if not title_column:
        print("Input file must contain one of these columns: Title, company_name, Company, Name, Business")
        return

    descriptions = []
    lead_scores = []

    for idx, row in df.iterrows():
        company_name = str(row[title_column]).strip()
        desc, score = smart_company_description_with_score(company_name, max_results=5)
        descriptions.append(desc)
        lead_scores.append(score)
        print(f"[📄 Done] {company_name} (Score: {score}/100)")

    df["Description"] = descriptions
    df["Lead_Score"] = lead_scores

    # Sort by lead score (highest first) for better prioritization
    df = df.sort_values('Lead_Score', ascending=False).reset_index(drop=True)
    df.to_excel(output_file, index=False)
    print(f"\n[SUCCESS] Smart Descriptions saved to: {output_file}")
    return output_file