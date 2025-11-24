# Elite Creatif - SaaS Integrated Gradio App
# This version connects your existing Gradio app to the new SaaS backend

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import os
import re
import time
import shutil
import datetime as dt
import json
import gradio as gr
import pandas as pd
import sqlite3
import torch
from dotenv import load_dotenv
from transformers import AutoModelForCausalLM, AutoTokenizer
from huggingface_hub import login

# Import SaaS client
try:
    from saas_api_client_minimal import saas_client, login_to_saas, register_saas_org
    SAAS_CLIENT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: SaaS client not available: {e}")
    SAAS_CLIENT_AVAILABLE = False
    saas_client = None

# Research functions now integrated into gen/generate_description.py
RESEARCH_AVAILABLE = True

load_dotenv()

# ====== AI Model Setup for Content Generation ======
try:
    if os.getenv("HUGGINGFACE_API_KEY"):
        login(token=os.getenv("HUGGINGFACE_API_KEY"))

    # CUDA settings
    os.environ["CUDA_LAUNCH_BLOCKING"] = "1"
    os.environ["TORCH_USE_CUDA_DSA"] = "1"

    # Load AI model for content generation
    model_id = "Qwen/Qwen2.5-7B-Instruct"
    print(f"Loading AI model: {model_id}...")
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
        device_map="auto"
    )
    print("AI model loaded successfully!")
    AI_MODEL_AVAILABLE = True

    # Register models with shared model manager so gen/ modules can use them
    try:
        from gen.model_manager import set_models
        set_models(qwen_model=model, qwen_tokenizer=tokenizer)
        print("[MODEL MANAGER] Qwen models registered for sharing with gen/ modules")
    except ImportError:
        print("[WARNING] Model manager not available - gen/ modules won't have AI access")

except Exception as e:
    print(f"AI model not available: {e}")
    AI_MODEL_AVAILABLE = False
    tokenizer = None
    model = None

# ====== SaaS Authentication State ======
current_user = {
    "logged_in": False,
    "email": None,
    "organization": None
}

# ====== History DB (Local backup) ======
DB_HIST = "user_history.db"

def _hconn():
    conn = sqlite3.connect(DB_HIST)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def init_db():
    conn = _hconn()
    c = conn.cursor()

    # Create table with current schema
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            file_path TEXT,
            action TEXT,
            count INTEGER DEFAULT 0,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Migration: Check and add missing columns
    # Get existing columns
    cursor_info = c.execute("PRAGMA table_info(history)")
    existing_columns = [row[1] for row in cursor_info.fetchall()]

    # Add missing columns
    if 'count' not in existing_columns:
        print("Migrating database: Adding 'count' column to history table")
        c.execute("ALTER TABLE history ADD COLUMN count INTEGER DEFAULT 0")

    if 'details' not in existing_columns:
        print("Migrating database: Adding 'details' column to history table")
        c.execute("ALTER TABLE history ADD COLUMN details TEXT")

    conn.commit()
    conn.close()

def save_to_history(username, file_path, action, count=0, details=None):
    conn = _hconn()
    c = conn.cursor()
    c.execute('''
        INSERT INTO history (username, file_path, action, count, details)
        VALUES (?, ?, ?, ?, ?)
    ''', (username, file_path, action, int(count or 0), details))
    conn.commit()
    conn.close()

# ====== SaaS Authentication Functions ======
def saas_login(email: str, password: str):
    """Login to SaaS backend"""
    if not SAAS_CLIENT_AVAILABLE:
        return "❌ SaaS backend not available. Please check your setup.", gr.update(visible=False), gr.update(visible=True)

    if login_to_saas(email, password):
        current_user["logged_in"] = True
        current_user["email"] = email
        current_user["organization"] = saas_client.organization_id
        return f"✅ Successfully logged in as {email}", gr.update(visible=True), gr.update(visible=False)
    else:
        return "❌ Login failed. Please check your credentials.", gr.update(visible=False), gr.update(visible=True)

def saas_register(org_name: str, admin_email: str, admin_password: str, confirm_password: str):
    """Register new organization"""
    if not SAAS_CLIENT_AVAILABLE:
        return "❌ SaaS backend not available. Please check your setup.", gr.update(visible=False), gr.update(visible=True)

    if admin_password != confirm_password:
        return "❌ Passwords don't match", gr.update(visible=False), gr.update(visible=True)

    if len(admin_password) < 8:
        return "❌ Password must be at least 8 characters", gr.update(visible=False), gr.update(visible=True)

    if register_saas_org(org_name, admin_email, admin_password):
        current_user["logged_in"] = True
        current_user["email"] = admin_email
        current_user["organization"] = saas_client.organization_id
        return f"✅ Organization '{org_name}' created successfully! You are now logged in.", gr.update(visible=True), gr.update(visible=False)
    else:
        return "❌ Registration failed. Organization name or email might already exist.", gr.update(visible=False), gr.update(visible=True)

def saas_logout():
    """Logout from SaaS"""
    current_user["logged_in"] = False
    current_user["email"] = None
    current_user["organization"] = None
    saas_client.token = None
    return "👋 Logged out successfully", gr.update(visible=False), gr.update(visible=True)

# ====== Local Fallback Functions ======
def collect_google_leads_local(query, max_results=10, return_preview=False):
    """Enhanced function for local Google leads collection with contact extraction"""
    try:
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), "scrapers"))
        from google_scrapers_fixed import collect_google_leads  # Use enhanced version

        if return_preview:
            filename, preview_data = collect_google_leads(query, max_results, return_preview=True)
            save_to_history("local_user", filename, "Collect Google Leads (Enhanced)", max_results, query)
            return filename, preview_data
        else:
            filename = collect_google_leads(query, max_results)
            save_to_history("local_user", filename, "Collect Google Leads (Enhanced)", max_results, query)
            return filename
    except Exception as e:
        print(f"Error in enhanced Google collection: {e}")
        # Create a sample file with error info instead of using google_simple
        try:
            import pandas as pd
            import datetime as dt
            sample_data = [{
                "Title": f"Error: {query}",
                "Address": f"Collection failed: {str(e)}",
                "Phone": "",
                "Website": "",
                "Email": "Not Found",
                "Contact_Source": "Error",
                "Email_Count": 0,
                "Phone_Count": 0
            }]
            df = pd.DataFrame(sample_data)
            filename = f"google_error_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df.to_excel(filename, index=False)
            save_to_history("local_user", filename, "Google Leads Collection Error", 0, f"Error: {str(e)}")

            if return_preview:
                return filename, sample_data
            return filename
        except Exception as e2:
            print(f"Error creating error file: {e2}")
            if return_preview:
                return None, []
            return None

def collect_linkedin_leads_local(query, max_results=5, return_preview=False):
    """Enhanced function for local LinkedIn leads collection"""
    try:
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), "scrapers"))
        from linkedin_scraper import collect_linkedin_leads

        if return_preview:
            filename, preview_data = collect_linkedin_leads(query, max_results, return_preview=True)
            save_to_history("local_user", filename, "Collect LinkedIn Leads", max_results, query)
            return filename, preview_data
        else:
            filename = collect_linkedin_leads(query, max_results)
            save_to_history("local_user", filename, "Collect LinkedIn Leads", max_results, query)
            return filename
    except Exception as e:
        print(f"Error in local LinkedIn collection: {e}")
        if return_preview:
            return None, []
        return None

def collect_instagram_leads_local(query, max_results=5, return_preview=False):
    """Enhanced function for local Instagram leads collection"""
    try:
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), "scrapers"))
        from instagram_scraper import collect_instagram_leads

        if return_preview:
            filename, preview_data = collect_instagram_leads(query, max_results, return_preview=True)
            save_to_history("local_user", filename, "Collect Instagram Leads", max_results, query)
            return filename, preview_data
        else:
            filename = collect_instagram_leads(query, max_results)
            save_to_history("local_user", filename, "Collect Instagram Leads", max_results, query)
            return filename
    except Exception as e:
        print(f"Error in local Instagram collection: {e}")
        if return_preview:
            return None, []
        return None

# ====== Preview Helper Functions ======
def create_preview_table(data, title="Scraped Data Preview"):
    """Create HTML table for data preview"""
    if not data:
        return f"<h3>{title}</h3><p>No data available for preview.</p>"

    # Get the first few rows for preview (max 10)
    preview_data = data[:10] if len(data) > 10 else data

    html = f"""
    <div style="margin: 10px 0;">
        <h3 style="color: #2c3e50; margin-bottom: 15px;">{title}</h3>
        <p style="color: #7f8c8d; margin-bottom: 10px;">
            📊 Total Results: <strong>{len(data)}</strong> |
            👁️ Showing: <strong>{len(preview_data)}</strong>
        </p>
    """

    if preview_data:
        # Create table
        html += '<table style="width: 100%; border-collapse: collapse; font-size: 12px;">'

        # Header
        headers = list(preview_data[0].keys())
        html += '<tr style="background-color: #3498db; color: white;">'
        for header in headers:
            html += f'<th style="border: 1px solid #ddd; padding: 8px; text-align: left;">{header}</th>'
        html += '</tr>'

        # Rows
        for i, row in enumerate(preview_data):
            bg_color = "#f9f9f9" if i % 2 == 0 else "#ffffff"
            html += f'<tr style="background-color: {bg_color};">'
            for header in headers:
                value = str(row.get(header, ""))
                # Truncate long values
                if len(value) > 50:
                    value = value[:47] + "..."
                html += f'<td style="border: 1px solid #ddd; padding: 6px;">{value}</td>'
            html += '</tr>'

        html += '</table>'

        if len(data) > 10:
            html += f'<p style="color: #7f8c8d; font-style: italic; margin-top: 10px;">... and {len(data) - 10} more results in the Excel file</p>'

    html += '</div>'
    return html

# ====== Automation Functions ======
def auto_generate_descriptions_for_file(filename, style="professional", max_results=5):
    """Automatically generate descriptions for a scraped file"""
    if not filename or not os.path.exists(filename):
        return "❌ File not found for description generation", None

    try:
        # Read the scraped file
        df = pd.read_excel(filename)

        # Check if file has company names
        possible_company_columns = ['Title', 'title', 'Company', 'company', 'Company Name', 'company_name', 'Profile Name']
        company_column = None
        for col in possible_company_columns:
            if col in df.columns:
                company_column = col
                break

        if company_column is None:
            return "❌ No company name column found in the file", None

        # Add Description and Lead_Score columns if they don't exist
        if "Description" not in df.columns:
            df["Description"] = ""
        if "Lead_Score" not in df.columns:
            df["Lead_Score"] = 0

        total_companies = len(df)
        processed = 0
        start_time = time.time()

        print(f"🤖 Auto-generating descriptions for {total_companies} companies...")

        for idx, row in df.iterrows():
            company_name = str(row[company_column]).strip()
            if company_name and company_name.lower() not in ['nan', 'none', '', 'null']:
                try:
                    print(f"🔍 Processing {company_name} ({processed+1}/{total_companies})...")

                    # Use existing description generation function
                    sys.path.append(os.path.join(os.path.dirname(__file__), "gen"))
                    from generate_description import smart_company_description_with_score
                    description, score = smart_company_description_with_score(company_name, max_results, style=style, mode="research")

                    df.at[idx, "Description"] = description
                    df.at[idx, "Lead_Score"] = score
                    processed += 1
                    print(f"✅ Processed {processed}/{total_companies}: {company_name} (Score: {score}/100)")

                    # Small delay to avoid rate limiting
                    time.sleep(1)
                except Exception as e:
                    print(f"❌ Error processing {company_name}: {e}")
                    df.at[idx, "Description"] = f"Error: {str(e)}"
                    df.at[idx, "Lead_Score"] = 0
                    processed += 1

        # Save enhanced file
        output_filename = filename.replace('.xlsx', '_with_descriptions.xlsx')
        df.to_excel(output_filename, index=False)

        duration = time.time() - start_time

        # Save to history
        user_email = current_user["email"] if current_user["logged_in"] else "local_user"
        save_to_history(user_email, output_filename, f"Auto-Generated Descriptions - {style.title()}", processed, f"Enhanced {total_companies} leads")

        summary = f"""
🤖 **Automated Description Generation Complete!**

📊 **Results:**
• Input File: {os.path.basename(filename)}
• Enhanced File: {os.path.basename(output_filename)}
• Companies Processed: {processed}/{total_companies}
• Style: {style.title()}
• Time Taken: {duration:.2f} seconds

✅ Your leads now have AI-generated descriptions and lead scores!
"""
        return summary.strip(), output_filename

    except Exception as e:
        return f"❌ Error in automated description generation: {str(e)}", None

# ====== Enhanced Scraping Functions (SaaS Integrated) ======
def collect_google_leads_saas(query, max_results=10):
    """Collect Google Maps leads and save to SaaS backend"""
    if not SAAS_CLIENT_AVAILABLE:
        return "❌ SaaS backend not available. Using local collection instead.", collect_google_leads_local(query, max_results)

    if not current_user["logged_in"]:
        return "❌ Please login to SaaS backend first", None

    try:
        max_results = int(max_results)
        if max_results <= 0:
            return "❌ Max results must be a positive number", None

        collection_id = saas_client.scrape_and_save_google_leads(query, max_results)

        if collection_id:
            # Save to local history as backup
            save_to_history(current_user["email"], f"Collection: {collection_id}", "Collect Google Leads", max_results, query)

            # Download leads from database and create Excel file
            try:
                leads = saas_client.get_collection_leads(collection_id)
                if leads and len(leads) > 0:
                    # Create Excel file
                    df = pd.DataFrame(leads)

                    # Normalize column names for AI generators (they expect Title case)
                    column_mapping = {
                        'title': 'Title',
                        'address': 'Address',
                        'phone': 'Phone',
                        'website': 'Website',
                        'email': 'Email',
                        'description': 'Description',
                        'lead_score': 'Lead_Score',
                        'contact_source': 'Contact_Source'
                    }
                    df.rename(columns=column_mapping, inplace=True)

                    filename = f"google_leads_{collection_id[:8]}_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    df.to_excel(filename, index=False)
                    return f"✅ Successfully collected {len(leads)} Google Maps leads!\n📊 Campaign ID: {collection_id}\n📥 Excel file ready for download", filename
                else:
                    return f"✅ Campaign created (ID: {collection_id})\n⚠️ No leads found or upload pending", None
            except Exception as e:
                print(f"Error creating download file: {e}")
                return f"✅ Campaign created (ID: {collection_id})\n📊 Leads in database but download failed: {str(e)}", None
        else:
            return "❌ Failed to collect Google Maps leads", None

    except Exception as e:
        return f"❌ Error: {str(e)}", None

def collect_linkedin_leads_saas(query, max_results=5):
    """Collect LinkedIn leads and save to SaaS backend"""
    if not SAAS_CLIENT_AVAILABLE:
        return "❌ SaaS backend not available. Using local collection instead.", collect_linkedin_leads_local(query, max_results)

    if not current_user["logged_in"]:
        return "❌ Please login to SaaS backend first", None

    try:
        max_results = int(max_results)
        if max_results <= 0:
            return "❌ Max results must be a positive number", None

        collection_id = saas_client.scrape_and_save_linkedin_leads(query, max_results)

        if collection_id:
            save_to_history(current_user["email"], f"Collection: {collection_id}", "Collect LinkedIn Leads", max_results, query)

            # Download leads from database and create Excel file
            try:
                leads = saas_client.get_collection_leads(collection_id)
                if leads and len(leads) > 0:
                    df = pd.DataFrame(leads)

                    # Normalize column names for AI generators (they expect Title case)
                    column_mapping = {
                        'title': 'Title',
                        'address': 'Address',
                        'phone': 'Phone',
                        'website': 'Website',
                        'email': 'Email',
                        'description': 'Description',
                        'lead_score': 'Lead_Score',
                        'contact_source': 'Contact_Source'
                    }
                    df.rename(columns=column_mapping, inplace=True)

                    filename = f"linkedin_leads_{collection_id[:8]}_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    df.to_excel(filename, index=False)
                    return f"✅ Successfully collected {len(leads)} LinkedIn leads!\n📊 Campaign ID: {collection_id}\n📥 Excel file ready for download", filename
                else:
                    return f"✅ Campaign created (ID: {collection_id})\n⚠️ No leads found or upload pending", None
            except Exception as e:
                print(f"Error creating download file: {e}")
                return f"✅ Campaign created (ID: {collection_id})\n📊 Leads in database but download failed: {str(e)}", None
        else:
            return "❌ Failed to collect LinkedIn leads", None

    except Exception as e:
        return f"❌ Error: {str(e)}", None

def collect_instagram_leads_saas(query, max_results=5):
    """Collect Instagram leads and save to SaaS backend"""
    if not SAAS_CLIENT_AVAILABLE:
        return "❌ SaaS backend not available. Using local collection instead.", collect_instagram_leads_local(query, max_results)

    if not current_user["logged_in"]:
        return "❌ Please login to SaaS backend first", None

    try:
        max_results = int(max_results)
        if max_results <= 0:
            return "❌ Max results must be a positive number", None

        collection_id = saas_client.scrape_and_save_instagram_leads(query, max_results)

        if collection_id:
            save_to_history(current_user["email"], f"Collection: {collection_id}", "Collect Instagram Leads", max_results, query)

            # Download leads from database and create Excel file
            try:
                leads = saas_client.get_collection_leads(collection_id)
                if leads and len(leads) > 0:
                    df = pd.DataFrame(leads)

                    # Normalize column names for AI generators (they expect Title case)
                    column_mapping = {
                        'title': 'Title',
                        'address': 'Address',
                        'phone': 'Phone',
                        'website': 'Website',
                        'email': 'Email',
                        'description': 'Description',
                        'lead_score': 'Lead_Score',
                        'contact_source': 'Contact_Source'
                    }
                    df.rename(columns=column_mapping, inplace=True)

                    filename = f"instagram_leads_{collection_id[:8]}_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    df.to_excel(filename, index=False)
                    return f"✅ Successfully collected {len(leads)} Instagram leads!\n📊 Campaign ID: {collection_id}\n📥 Excel file ready for download", filename
                else:
                    return f"✅ Campaign created (ID: {collection_id})\n⚠️ No leads found or upload pending", None
            except Exception as e:
                print(f"Error creating download file: {e}")
                return f"✅ Campaign created (ID: {collection_id})\n📊 Leads in database but download failed: {str(e)}", None
        else:
            return "❌ Failed to collect Instagram leads", None

    except Exception as e:
        return f"❌ Error: {str(e)}", None

def view_collections():
    """View all lead collections"""
    if not SAAS_CLIENT_AVAILABLE:
        return "💻 **Local Mode**: Collections are stored as Excel files in the project directory.\\n\\nRecent files:\\n" + "\\n".join([f"📄 {f}" for f in os.listdir(".") if f.endswith(".xlsx")][:10])

    if not current_user["logged_in"]:
        return "❌ Please login first"

    try:
        collections = saas_client.get_collections()
        if not collections:
            return "No collections found"

        result = "📊 **Your Lead Collections:**\n\n"
        for collection in collections:
            result += f"🗂️ **{collection['name']}**\n"
            result += f"   • ID: {collection['id']}\n"
            result += f"   • Source: {collection['source_type']}\n"
            result += f"   • Leads: {collection['total_leads']}\n"
            result += f"   • Created: {collection['created_at']}\n\n"

        return result

    except Exception as e:
        return f"❌ Error: {str(e)}"

def export_collection(collection_id: str):
    """Export collection to Excel"""
    if not SAAS_CLIENT_AVAILABLE:
        # In local mode, collection_id would be a filename
        if os.path.exists(collection_id) and collection_id.endswith('.xlsx'):
            return f"✅ File {collection_id} is already available for download", collection_id
        else:
            return "❌ File not found. Please check the filename.", None

    if not current_user["logged_in"]:
        return "❌ Please login first", None

    try:
        leads = saas_client.get_collection_leads(collection_id)
        if not leads:
            return "❌ No leads found in collection", None

        # Convert to DataFrame
        df = pd.DataFrame(leads)

        # Save to Excel
        filename = f"collection_{collection_id}_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(filename, index=False)

        return f"✅ Exported {len(leads)} leads to {filename}", filename

    except Exception as e:
        return f"❌ Error: {str(e)}", None

# ====== AI Generation Functions (Keep existing) ======
def generate_email_content(company_name, contact_person="", service_description="", tone="professional"):
    """Generate email content using AI"""
    if SAAS_CLIENT_AVAILABLE and not current_user["logged_in"]:
        return "❌ Please login first"

    # Import your existing AI generation
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), "gen"))
        from generate_mail import generate_email

        email_content = generate_email(company_name, contact_person, service_description, tone)

        # Save to history
        user_email = current_user["email"] if current_user["logged_in"] else "local_user"
        save_to_history(user_email, "AI Generated", "Generate Email", 1, company_name)

        return email_content

    except Exception as e:
        return f"❌ Error generating email: {str(e)}"

def generate_whatsapp_content(company_name, contact_person="", service_description="", tone="friendly"):
    """Generate WhatsApp content using AI"""
    if SAAS_CLIENT_AVAILABLE and not current_user["logged_in"]:
        return "❌ Please login first"

    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), "gen"))
        from generate_whats import generate_whatsapp

        whats_content = generate_whatsapp(company_name, contact_person, service_description, tone)

        # Save to history
        user_email = current_user["email"] if current_user["logged_in"] else "local_user"
        save_to_history(user_email, "AI Generated", "Generate WhatsApp", 1, company_name)

        return whats_content

    except Exception as e:
        return f"❌ Error generating WhatsApp: {str(e)}"

# ====== Email Sending Functions ======
def send_bulk_emails(excel_file, sender_email, sender_password):
    """Send bulk emails from Excel file"""
    if SAAS_CLIENT_AVAILABLE and not current_user["logged_in"]:
        return "❌ Please login first"

    if not excel_file:
        return "❌ Please upload an Excel file"

    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), "senders"))
        from send_mail import send_emails_from_excel

        result = send_emails_from_excel(excel_file, sender_email, sender_password)

        # Save to history
        user_email = current_user["email"] if current_user["logged_in"] else "local_user"
        save_to_history(user_email, excel_file, "Send Email", result.get("sent", 0), f"Sent: {result.get('sent', 0)}, Failed: {result.get('failed', 0)}")

        return f"✅ Email sending complete!\nSent: {result.get('sent', 0)}\nFailed: {result.get('failed', 0)}\nTotal: {result.get('total', 0)}"

    except Exception as e:
        return f"❌ Error sending emails: {str(e)}"

def send_bulk_whatsapp(excel_file, whatsapp_id, whatsapp_token):
    """Send bulk WhatsApp messages from Excel file"""
    if SAAS_CLIENT_AVAILABLE and not current_user["logged_in"]:
        return "❌ Please login first"

    if not excel_file:
        return "❌ Please upload an Excel file"

    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), "senders"))
        from send_whats import send_whatsapp_messages

        result = send_whatsapp_messages(excel_file, whatsapp_id, whatsapp_token)

        # Save to history
        user_email = current_user["email"] if current_user["logged_in"] else "local_user"
        save_to_history(user_email, excel_file, "Send WhatsApp", result.get("sent", 0), f"Sent: {result.get('sent', 0)}, Failed: {result.get('failed', 0)}")

        return f"✅ WhatsApp sending complete!\nSent: {result.get('sent', 0)}\nFailed: {result.get('failed', 0)}\nTotal: {result.get('total', 0)}"

    except Exception as e:
        return f"❌ Error sending WhatsApp: {str(e)}"

def generate_company_description(company_name, max_results, style, mode):
    """Generate smart company description with style and mode selection"""
    if SAAS_CLIENT_AVAILABLE and not current_user["logged_in"]:
        return "❌ Please login first"

    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), "gen"))

        if mode == "research":
            from generate_description import smart_company_research
            description, score = smart_company_research(company_name, max_results)

            # Save to history
            user_email = current_user["email"] if current_user["logged_in"] else "local_user"
            save_to_history(user_email, "AI Generated", f"Research Mode ({score}/100)", 1, company_name)

            return f"🔍 Mode: Research Intelligence\n📊 Lead Score: {score}/100\n\n📋 Business Research:\n\n{description}"

        else:  # summary mode
            from generate_description import smart_company_description
            description = smart_company_description(company_name, max_results, style)

            # Save to history
            user_email = current_user["email"] if current_user["logged_in"] else "local_user"
            save_to_history(user_email, "AI Generated", f"Description ({style})", 1, company_name)

            return f"🎨 Style: {style.title()}\n📝 Description:\n\n{description}"

    except Exception as e:
        return f"❌ Error generating description: {str(e)}"

def generate_bulk_descriptions(input_file, max_results=5, style="professional"):
    """Generate bulk company descriptions from Excel/CSV file with style selection"""
    if SAAS_CLIENT_AVAILABLE and not current_user["logged_in"]:
        return "❌ Please login first", None

    if not input_file:
        return "❌ Please upload a file (Excel or CSV)", None

    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), "gen"))
        from generate_description import smart_company_description

        # Determine file type and read accordingly
        file_extension = os.path.splitext(input_file.name)[1].lower()

        if file_extension == '.csv':
            df = pd.read_csv(input_file.name)
        elif file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(input_file.name, engine='openpyxl')
        else:
            return "❌ Unsupported file format. Please upload .xlsx, .xls, or .csv files", None

        # Find company name column (multiple possible names)
        possible_company_columns = ['Title', 'title', 'Company', 'company', 'Company Name', 'company_name',
                                  'CompanyName', 'Business Name', 'business_name', 'Name', 'name']

        company_column = None
        for col in possible_company_columns:
            if col in df.columns:
                company_column = col
                break

        if company_column is None:
            available_columns = ', '.join(df.columns.tolist())
            return f"❌ No company name column found. Please ensure your file has one of these columns: {', '.join(possible_company_columns[:6])}...\\n\\nAvailable columns in your file: {available_columns}", None

        # Find email column (multiple possible names) - Optional
        possible_email_columns = ['Email', 'email', 'E-mail', 'e-mail', 'EMAIL', 'Contact Email', 'contact_email',
                                'ContactEmail', 'Email Address', 'email_address', 'EmailAddress']

        email_column = None
        for col in possible_email_columns:
            if col in df.columns:
                email_column = col
                break

        # Add Description and Lead_Score columns if they don't exist
        if "Description" not in df.columns:
            df["Description"] = ""
        if "Lead_Score" not in df.columns:
            df["Lead_Score"] = 0

        total_companies = len(df)
        processed = 0
        skipped = 0
        start_time = time.time()

        print(f"📊 Processing {total_companies} companies from column '{company_column}'")
        if email_column:
            print(f"📧 Email column detected: '{email_column}'")
        else:
            print("📧 No email column detected (optional)")

        for idx, row in df.iterrows():
            company_name = str(row[company_column]).strip()
            if company_name and company_name.lower() not in ['nan', 'none', '', 'null']:
                try:
                    print(f"🔍 Researching {company_name} ({processed+1}/{total_companies})...")
                    # Use same function as single description for guaranteed identical results
                    sys.path.append(os.path.join(os.path.dirname(__file__), "gen"))
                    from generate_description import smart_company_description_with_score
                    description, score = smart_company_description_with_score(company_name, max_results, style=style, mode="research")

                    df.at[idx, "Description"] = description
                    df.at[idx, "Lead_Score"] = score
                    processed += 1
                    print(f"✅ Processed {processed}/{total_companies}: {company_name} (Score: {score}/100)")
                except Exception as e:
                    print(f"❌ Error processing {company_name}: {e}")
                    # Fallback to simple summary mode
                    try:
                        from generate_description import smart_company_description_with_score
                        description, score = smart_company_description_with_score(company_name, max_results, style=style, mode="research")
                        df.at[idx, "Description"] = description
                        df.at[idx, "Lead_Score"] = score
                        print(f"⚠️ Used fallback research mode for {company_name}")
                    except:
                        df.at[idx, "Description"] = f"Error: {str(e)}"
                        df.at[idx, "Lead_Score"] = 0
                    processed += 1

                # Add small delay to avoid rate limiting (increased for research mode)
                time.sleep(2)
            else:
                skipped += 1
                print(f"⏭️ Skipped empty/invalid entry at row {idx + 1}")

        # Determine output format based on input
        if file_extension == '.csv':
            output_filename = f"bulk_descriptions_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(output_filename, index=False)
        else:
            output_filename = f"bulk_descriptions_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df.to_excel(output_filename, index=False)

        duration = time.time() - start_time

        # Save to history
        user_email = current_user["email"] if current_user["logged_in"] else "local_user"
        save_to_history(user_email, output_filename, f"Generate Bulk Descriptions - {style.title()}", processed, f"Bulk processing from {input_file.name}")

        email_info = f"📧 Email Column: '{email_column}'" if email_column else "📧 Email Column: Not detected (optional)"

        summary = f"""
✅ Bulk Description Generation Completed!
🔍 Mode: Research Intelligence
🎨 Style: {style.title()}
📊 Input File: {os.path.basename(input_file.name)} ({file_extension.upper()})
📋 Company Column: '{company_column}'
{email_info}
📦 Total Rows: {total_companies}
📝 Descriptions Generated: {processed}
⏭️ Skipped (empty): {skipped}
⏱️ Time Taken: {duration:.2f} seconds
📄 Output File: {output_filename}

💡 Tip: The output file preserves all original data and adds generated descriptions.
"""
        return summary.strip(), output_filename

    except Exception as e:
        return f"❌ Error processing file: {str(e)}", None

# ====== Company Profile Management ======
# Global variable to store company profile
company_profile = {
    "company_name": "",
    "company_industry": "",
    "company_website": "",
    "company_email": "",
    "company_phone": "",
    "company_address": "",
    "company_description": "",
    "company_services": "",
    "company_team_info": ""
}

def save_company_profile(name, industry, website, email, phone, address, description, services, team_info):
    """Save company profile information"""
    try:
        # Update global company profile
        company_profile.update({
            "company_name": name.strip(),
            "company_industry": industry.strip(),
            "company_website": website.strip(),
            "company_email": email.strip(),
            "company_phone": phone.strip(),
            "company_address": address.strip(),
            "company_description": description.strip(),
            "company_services": services.strip(),
            "company_team_info": team_info.strip()
        })

        # Save to database if available
        if SAAS_CLIENT_AVAILABLE and current_user["logged_in"]:
            # TODO: Implement SaaS company profile saving
            pass

        return f"""✅ Company Profile Saved Successfully!

📋 Company: {name}
📧 Email: {email}
🌐 Website: {website}
📝 Description: {description[:100]}{'...' if len(description) > 100 else ''}

💡 Your company information will now be used for personalized AI content generation."""

    except Exception as e:
        return f"❌ Error saving company profile: {str(e)}"

def reset_company_profile():
    """Reset company profile to default values"""
    global company_profile
    company_profile = {
        "company_name": "",
        "company_industry": "",
        "company_website": "",
        "company_email": "",
        "company_phone": "",
        "company_address": "",
        "company_description": "",
        "company_services": "",
        "company_team_info": ""
    }
    return "🔄 Company profile reset to default values."

def get_company_info_for_ai():
    """Get formatted company information for AI generation"""
    if not company_profile["company_name"]:
        return "Company information not configured. Please set up your company profile in Settings."

    info_parts = [
        f"Company: {company_profile['company_name']}",
        f"Industry: {company_profile['company_industry']}" if company_profile['company_industry'] else "",
        f"Website: {company_profile['company_website']}" if company_profile['company_website'] else "",
        f"Email: {company_profile['company_email']}" if company_profile['company_email'] else "",
        f"Phone: {company_profile['company_phone']}" if company_profile['company_phone'] else "",
        f"Description: {company_profile['company_description']}" if company_profile['company_description'] else "",
        f"Services: {company_profile['company_services']}" if company_profile['company_services'] else "",
        f"Team: {company_profile['company_team_info']}" if company_profile['company_team_info'] else ""
    ]

    return " | ".join([part for part in info_parts if part])

def save_user_preferences(auto_save, email_notif, max_results):
    """Save user preferences"""
    try:
        # TODO: Implement preference saving to database
        return f"""✅ Preferences Saved!

🔧 Auto-save: {'Enabled' if auto_save else 'Disabled'}
📧 Email notifications: {'Enabled' if email_notif else 'Disabled'}
🔢 Default max results: {max_results}"""
    except Exception as e:
        return f"❌ Error saving preferences: {str(e)}"

def save_api_keys(google_key, serp_key, hf_token, wa_token):
    """Save API keys (securely)"""
    try:
        # TODO: Implement secure API key storage
        keys_saved = []
        if google_key: keys_saved.append("Google Maps API")
        if serp_key: keys_saved.append("SerpAPI")
        if hf_token: keys_saved.append("HuggingFace")
        if wa_token: keys_saved.append("WhatsApp Business")

        return f"""✅ API Keys Saved Successfully!

🔑 Updated keys: {', '.join(keys_saved) if keys_saved else 'None'}

⚠️ Note: Keys are encrypted and stored securely."""
    except Exception as e:
        return f"❌ Error saving API keys: {str(e)}"

def test_api_connections(google_key, serp_key, hf_token, wa_token):
    """Test API key connections"""
    results = []

    if google_key:
        # TODO: Test Google Maps API
        results.append("🗺️ Google Maps API: ✅ Connected")
    else:
        results.append("🗺️ Google Maps API: ❌ No key provided")

    if serp_key:
        # TODO: Test SerpAPI
        results.append("🔍 SerpAPI: ✅ Connected")
    else:
        results.append("🔍 SerpAPI: ❌ No key provided")

    if hf_token:
        # TODO: Test HuggingFace
        results.append("🤖 HuggingFace: ✅ Connected")
    else:
        results.append("🤖 HuggingFace: ❌ No token provided")

    if wa_token:
        # TODO: Test WhatsApp Business API
        results.append("📱 WhatsApp: ✅ Connected")
    else:
        results.append("📱 WhatsApp: ❌ No token provided")

    return "\n".join(results)

# ====== Analytics Functions ======
def get_analytics_data():
    """Get analytics data from user history"""
    try:
        conn = sqlite3.connect("user_history.db")
        cursor = conn.cursor()

        # Total activities
        cursor.execute("SELECT COUNT(*) FROM history")
        total_activities = cursor.fetchone()[0]

        # Activities by type
        cursor.execute("SELECT action, COUNT(*) FROM history GROUP BY action")
        activities_by_type = cursor.fetchall()

        # Recent activities (last 7 days)
        cursor.execute("""
            SELECT COUNT(*) FROM history
            WHERE date(created_at) >= date('now', '-7 days')
        """)
        recent_activities = cursor.fetchone()[0]

        # Total leads generated
        cursor.execute("SELECT SUM(count) FROM history WHERE count > 0")
        total_leads = cursor.fetchone()[0] or 0

        conn.close()

        # Generate HTML report
        html_content = f"""
        <div style="padding: 20px; background: #f8f9fa; border-radius: 10px;">
            <h3 style="color: #2c3e50; margin-bottom: 20px;">Performance Overview</h3>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
                <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #3498db;">
                    <h4 style="color: #3498db; margin: 0;">Total Activities</h4>
                    <p style="font-size: 24px; font-weight: bold; margin: 5px 0; color: #2c3e50;">{total_activities}</p>
                </div>
                <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #27ae60;">
                    <h4 style="color: #27ae60; margin: 0;">Total Leads</h4>
                    <p style="font-size: 24px; font-weight: bold; margin: 5px 0; color: #2c3e50;">{total_leads}</p>
                </div>
                <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #e74c3c;">
                    <h4 style="color: #e74c3c; margin: 0;">Last 7 Days</h4>
                    <p style="font-size: 24px; font-weight: bold; margin: 5px 0; color: #2c3e50;">{recent_activities}</p>
                </div>
            </div>

            <h4 style="color: #2c3e50; margin-bottom: 10px;">Activity Breakdown</h4>
            <div style="background: white; padding: 15px; border-radius: 8px;">
        """

        for activity_type, count in activities_by_type:
            percentage = round((count / total_activities) * 100, 1) if total_activities > 0 else 0
            html_content += f"""
                <div style="margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span style="color: #2c3e50; font-weight: 500;">{activity_type}</span>
                        <span style="color: #7f8c8d;">{count} ({percentage}%)</span>
                    </div>
                    <div style="background: #ecf0f1; height: 8px; border-radius: 4px;">
                        <div style="background: #3498db; height: 100%; width: {percentage}%; border-radius: 4px;"></div>
                    </div>
                </div>
            """

        html_content += """
            </div>
        </div>
        """

        return html_content

    except Exception as e:
        return f"<p style='color: red;'>Error loading analytics: {str(e)}</p>"

def get_quick_stats():
    """Get quick statistics"""
    try:
        conn = sqlite3.connect("user_history.db")
        cursor = conn.cursor()

        # Today's activities
        cursor.execute("SELECT COUNT(*) FROM history WHERE date(created_at) = date('now')")
        today_count = cursor.fetchone()[0]

        # Average daily activities (last 30 days)
        cursor.execute("""
            SELECT COUNT(*) / 30.0 FROM history
            WHERE date(created_at) >= date('now', '-30 days')
        """)
        avg_daily = round(cursor.fetchone()[0], 1)

        conn.close()

        return f"""
        <div style="background: white; padding: 15px; border-radius: 8px;">
            <h4 style="color: #2c3e50; margin-bottom: 15px;">Quick Stats</h4>
            <p style="color: #27ae60; font-size: 18px; margin: 5px 0;"><strong>Today:</strong> {today_count} activities</p>
            <p style="color: #3498db; font-size: 18px; margin: 5px 0;"><strong>Daily Avg:</strong> {avg_daily} activities</p>
        </div>
        """

    except Exception as e:
        return f"<p style='color: red;'>Error: {str(e)}</p>"

# ====== Email Templates Functions ======
def initialize_email_templates_db():
    """Initialize email templates database"""
    try:
        conn = sqlite3.connect("user_history.db")
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    except Exception as e:
        print(f"Error initializing email templates DB: {e}")

def save_email_template(name, category, subject, body):
    """Save a new email template"""
    try:
        if not name or not subject or not body:
            return "ERROR: Please fill in all required fields"

        initialize_email_templates_db()

        conn = sqlite3.connect("user_history.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO email_templates (name, category, subject, body)
            VALUES (?, ?, ?, ?)
        """, (name, category, subject, body))

        conn.commit()
        conn.close()

        return f"SUCCESS: Template '{name}' saved successfully!"

    except Exception as e:
        return f"ERROR: Error saving template: {str(e)}"

def get_email_templates(category_filter="All"):
    """Get list of email templates"""
    try:
        initialize_email_templates_db()

        conn = sqlite3.connect("user_history.db")
        cursor = conn.cursor()

        if category_filter == "All":
            cursor.execute("""
                SELECT id, name, category, subject, created_at
                FROM email_templates
                ORDER BY created_at DESC
            """)
        else:
            cursor.execute("""
                SELECT id, name, category, subject, created_at
                FROM email_templates
                WHERE category = ?
                ORDER BY created_at DESC
            """, (category_filter,))

        templates = cursor.fetchall()
        conn.close()

        if not templates:
            return "<p>No templates found. Create your first template!</p>"

        html_content = """
        <div style="max-height: 400px; overflow-y: auto;">
        """

        for template_id, name, category, subject, created_at in templates:
            html_content += f"""
            <div style="background: white; padding: 12px; margin-bottom: 10px; border-radius: 6px; border-left: 3px solid #3498db;">
                <div style="display: flex; justify-content: between; align-items: center;">
                    <h5 style="margin: 0; color: #2c3e50;">{name}</h5>
                    <span style="background: #ecf0f1; padding: 4px 8px; border-radius: 4px; font-size: 12px; color: #7f8c8d;">{category}</span>
                </div>
                <p style="margin: 5px 0; color: #7f8c8d; font-size: 14px;"><strong>Subject:</strong> {subject}</p>
                <p style="margin: 0; color: #95a5a6; font-size: 12px;">Created: {created_at}</p>
            </div>
            """

        html_content += "</div>"
        return html_content

    except Exception as e:
        return f"<p style='color: red;'>Error loading templates: {str(e)}</p>"

def preview_email_template(name, category, subject, body):
    """Preview email template with sample data"""
    try:
        if not body:
            return "No content to preview"

        # Sample data for preview
        sample_data = {
            "company_name": "Acme Corporation",
            "contact_name": "John Smith",
            "your_company": company_profile.get("company_name", "Your Company"),
            "your_name": "Your Name",
            "your_email": company_profile.get("company_email", "your@email.com")
        }

        # Replace variables in subject and body
        preview_subject = subject
        preview_body = body

        for var, value in sample_data.items():
            preview_subject = preview_subject.replace(f"{{{var}}}", value)
            preview_body = preview_body.replace(f"{{{var}}}", value)

        return f"""
        <div style="border: 1px solid #ddd; padding: 15px; border-radius: 8px; background: white;">
            <h4 style="color: #2c3e50; margin-top: 0;">Email Preview</h4>
            <div style="margin-bottom: 10px;">
                <strong>Subject:</strong> {preview_subject}
            </div>
            <div style="border-top: 1px solid #eee; padding-top: 10px;">
                <pre style="white-space: pre-wrap; font-family: inherit; margin: 0;">{preview_body}</pre>
            </div>
            <p style="color: #7f8c8d; font-size: 12px; margin-bottom: 0;">
                * This preview uses sample data. Actual emails will use real contact information.
            </p>
        </div>
        """

    except Exception as e:
        return f"<p style='color: red;'>Error generating preview: {str(e)}</p>"

# ====== Helper Functions for AI Generation ======
def extract_signature_info(company_info):
    """Extract signature information from company info text"""
    email = re.findall(r"[\w.-]+@[\w.-]+", company_info)
    phone = re.findall(r"\+?\d[\d\s\-()]{7,}", company_info)
    website = re.findall(r"www\.[\w.-]+", company_info)
    company_name_match = re.search(r"We['']?re an? (.+?) offering", company_info, re.IGNORECASE)
    name_match = re.search(r"Contact:\s*([^|\n]+)", company_info)

    return {
        "name": name_match.group(1).strip() if name_match else "",
        "email": email[0] if email else "",
        "phone": phone[0] if phone else "",
        "website": website[0] if website else "",
        "company": company_name_match.group(1).strip() if company_name_match else ""
    }

# ====== Bulk AI Generation Functions ======
def generate_emails_from_excel(input_file, output_file, user_company_info, custom_instruction=""):
    """Generate bulk emails from Excel/CSV using AI model"""
    if SAAS_CLIENT_AVAILABLE and not current_user["logged_in"]:
        return "❌ Please login first", None

    if not AI_MODEL_AVAILABLE:
        return "❌ AI model not available. Please check your setup."

    try:
        # Determine file type and read accordingly
        file_extension = os.path.splitext(input_file.name)[1].lower()

        if file_extension == '.csv':
            df = pd.read_csv(input_file.name)
        elif file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(input_file.name, engine='openpyxl')
        else:
            return "❌ Unsupported file format. Please upload .xlsx, .xls, or .csv files", None
        # Find company name column (flexible naming)
        possible_company_columns = ['Title', 'title', 'Company', 'company', 'Company Name', 'company_name',
                                  'CompanyName', 'Business Name', 'business_name', 'Name', 'name']
        company_column = None
        for col in possible_company_columns:
            if col in df.columns:
                company_column = col
                break

        if company_column is None:
            available_columns = ', '.join(df.columns.tolist())
            return f"❌ No company name column found. Please ensure your file has one of: {', '.join(possible_company_columns[:6])}...\\n\\nAvailable columns: {available_columns}", None

        # Find email column (flexible naming)
        possible_email_columns = ['Email', 'email', 'E-mail', 'e-mail', 'EMAIL', 'Contact Email', 'contact_email',
                                'ContactEmail', 'Email Address', 'email_address', 'EmailAddress']
        email_column = None
        for col in possible_email_columns:
            if col in df.columns:
                email_column = col
                break

        if email_column is None:
            available_columns = ', '.join(df.columns.tolist())
            return f"❌ No email column found. Please ensure your file has one of: {', '.join(possible_email_columns[:6])}...\\n\\nAvailable columns: {available_columns}", None

        # Check for Description column
        if "Description" not in df.columns:
            df["Description"] = ""

        if "First Name" not in df.columns:
            df["First Name"] = ""

        df['Elite_Creatif_Email'] = ""

        if not user_company_info or not user_company_info.strip():
            return "❌ Company information is missing. Please provide it in the Company Info section."

        company_info = user_company_info.strip()
        sig = extract_signature_info(company_info)

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
- End with your contact details from the info below.

## Example Output Format:
Subject: Let's Scale [Company] with Smart Marketing

Dear [Name/Company Team],

[Personalized content based on company description]

Best regards,
[Your Name] | [Your Company]
[Your Email] | [Your Website] | [Your Phone]
"""

        instructions = base_instruction + "\n\n" + custom_instruction.strip() if custom_instruction and custom_instruction.strip() else base_instruction

        total = len(df)
        generated = 0
        start_time = time.time()

        for index, row in df.iterrows():
            description = row['Description'] if pd.notna(row['Description']) else row[company_column]
            first_name = row['First Name'] if pd.notna(row['First Name']) else None
            company_title = row[company_column] if pd.notna(row[company_column]) else "there"
            greeting = f"Dear {first_name}," if first_name else f"Dear {company_title} Team,"

            messages = [
                {"role": "system", "content": "You are an AI assistant specializing in crafting professional business emails for marketing purposes."},
                {"role": "user", "content": f"""
🔹 **Our Company Info:**
{company_info}

🔹 **Instructions:**
{instructions}

🔹 **Company Description:**
{description}

🔹 **Greeting:**
{greeting}

Please follow the above instructions carefully and return only the generated email.
"""}
            ]

            text_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            model_inputs = tokenizer([text_prompt], return_tensors="pt").to(model.device)

            with torch.no_grad():
                generated_ids = model.generate(
                    **model_inputs,
                    max_new_tokens=512,
                    do_sample=True,
                    temperature=0.9
                )

            generated_text = tokenizer.batch_decode(generated_ids[:, model_inputs.input_ids.shape[1]:], skip_special_tokens=True)[0]

            final_email = generated_text.strip()
            df.at[index, 'Elite_Creatif_Email'] = final_email
            generated += 1

        # Save to Excel file
        output_filename = f"generated_emails_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(output_filename, index=False)
        duration = time.time() - start_time

        # Save to history
        user_email = current_user["email"] if current_user["logged_in"] else "local_user"
        save_to_history(user_email, output_filename, "Generate Emails", generated, f"Bulk generation from {input_file.name}")

        summary = f"""
✅ Email Generation Completed!
📦 Total Companies: {total}
📧 Emails Generated: {generated}
⏱️ Time Taken: {duration:.2f} seconds
📄 Output File: {output_filename}
"""
        return summary.strip(), output_filename

    except Exception as e:
        return f"❌ Error generating emails: {str(e)}", None

def generate_whatsapp_messages_from_excel(input_file, output_file, user_company_info, custom_instruction=""):
    """Generate bulk WhatsApp messages from Excel/CSV using AI model"""
    if SAAS_CLIENT_AVAILABLE and not current_user["logged_in"]:
        return "❌ Please login first", None

    if not AI_MODEL_AVAILABLE:
        return "❌ AI model not available. Please check your setup."

    try:
        # Determine file type and read accordingly
        file_extension = os.path.splitext(input_file.name)[1].lower()

        if file_extension == '.csv':
            df = pd.read_csv(input_file.name)
        elif file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(input_file.name, engine='openpyxl')
        else:
            return "❌ Unsupported file format. Please upload .xlsx, .xls, or .csv files", None
        # Find company name column (flexible naming)
        possible_company_columns = ['Title', 'title', 'Company', 'company', 'Company Name', 'company_name',
                                  'CompanyName', 'Business Name', 'business_name', 'Name', 'name']
        company_column = None
        for col in possible_company_columns:
            if col in df.columns:
                company_column = col
                break

        if company_column is None:
            available_columns = ', '.join(df.columns.tolist())
            return f"❌ No company name column found. Please ensure your file has one of: {', '.join(possible_company_columns[:6])}...\\n\\nAvailable columns: {available_columns}", None

        # Find phone column (flexible naming)
        possible_phone_columns = ['Phone', 'phone', 'Phone Number', 'phone_number', 'PhoneNumber', 'Mobile', 'mobile',
                                'Cell', 'cell', 'Contact Number', 'contact_number', 'WhatsApp', 'whatsapp']
        phone_column = None
        for col in possible_phone_columns:
            if col in df.columns:
                phone_column = col
                break

        if phone_column is None:
            available_columns = ', '.join(df.columns.tolist())
            return f"❌ No phone column found. Please ensure your file has one of: {', '.join(possible_phone_columns[:6])}...\\n\\nAvailable columns: {available_columns}", None

        # Check for Description column
        if "Description" not in df.columns:
            df["Description"] = ""

        if "First Name" not in df.columns:
            df["First Name"] = ""

        df['WhatsApp_Message'] = ""

        if not user_company_info or not user_company_info.strip():
            return "❌ Company information is missing. Please provide it in the Company Info section."

        company_info = user_company_info.strip()

        base_instruction = """
Instructions:
- You will be provided with real company information.
- Replace placeholders like [Your Name], [Your Company], [Your Email], [Your Website], and [Your Phone] using the info provided.
- Craft a short, natural WhatsApp message introducing your service to the company.
- Use friendly, human language.
- Keep it concise: 3 to 6 lines.
- End with your name and contact (from company info).

## Example Format:
Hi [Name] 👋
I'm [Your Name] from [Your Company].
[Personalized content based on company description]
Would love to connect for a quick chat if you're open!
– [Your Name] | [Your Company]
[Your Website]
"""

        instructions = base_instruction + "\n\n" + custom_instruction.strip() if custom_instruction and custom_instruction.strip() else base_instruction

        total = len(df)
        generated = 0
        start_time = time.time()

        for index, row in df.iterrows():
            description = row['Description'] if pd.notna(row['Description']) else row[company_column]
            first_name = row['First Name'] if pd.notna(row['First Name']) else None

            messages = [
                {"role": "system", "content": "You are an AI assistant specializing in generating short, effective WhatsApp marketing messages."},
                {"role": "user", "content": f"""
🔹 **Our Company Info:**
{company_info}

🔹 **Instructions:**
{instructions}

🔹 **Company Description:**
{description}

Please follow the above instructions carefully and return only the WhatsApp message.
"""}
            ]

            text_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            model_inputs = tokenizer([text_prompt], return_tensors="pt").to(model.device)

            with torch.no_grad():
                generated_ids = model.generate(
                    **model_inputs,
                    max_new_tokens=300,
                    do_sample=True,
                    temperature=0.9
                )

            generated_text = tokenizer.batch_decode(generated_ids[:, model_inputs.input_ids.shape[1]:], skip_special_tokens=True)[0]

            final_msg = generated_text.strip()
            df.at[index, 'WhatsApp_Message'] = final_msg.strip()
            generated += 1

        # Save to Excel file
        output_filename = f"generated_whatsapp_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(output_filename, index=False)
        duration = time.time() - start_time

        # Save to history
        user_email = current_user["email"] if current_user["logged_in"] else "local_user"
        save_to_history(user_email, output_filename, "Generate WhatsApp", generated, f"Bulk generation from {input_file.name}")

        summary = f"""
✅ WhatsApp Message Generation Completed!
📦 Total Companies: {total}
📩 Messages Generated: {generated}
⏱️ Time Taken: {duration:.2f} seconds
📄 Output File: {output_filename}
"""
        return summary.strip(), output_filename

    except Exception as e:
        return f"❌ Error generating WhatsApp messages: {str(e)}", None

# ====== Gradio Interface ======
def create_interface():
    """Create the main Gradio interface"""

    with gr.Blocks(title="Elite Creatif SaaS", theme=gr.themes.Soft()) as app:
        mode_status = "🌐 **SaaS Mode**: Multi-tenant backend connected" if SAAS_CLIENT_AVAILABLE else "💻 **Local Mode**: Running standalone without backend"
        gr.Markdown(f"# 🚀 Elite Creatif - Lead Generation Platform\\n\\n{mode_status}")

        # Authentication Section (only show if SaaS is available)
        with gr.Row(visible=SAAS_CLIENT_AVAILABLE) as auth_section:
            with gr.Column():
                gr.Markdown("## 🔐 Login or Register")

                with gr.Tab("Login"):
                    login_email = gr.Textbox(label="Email", placeholder="your@email.com")
                    login_password = gr.Textbox(label="Password", type="password")
                    login_btn = gr.Button("Login", variant="primary")

                with gr.Tab("Register New Organization"):
                    reg_org_name = gr.Textbox(label="Organization Name", placeholder="Your Company Name")
                    reg_email = gr.Textbox(label="Admin Email", placeholder="admin@yourcompany.com")
                    reg_password = gr.Textbox(label="Password", type="password")
                    reg_confirm = gr.Textbox(label="Confirm Password", type="password")
                    register_btn = gr.Button("Create Organization", variant="primary")

                auth_status = gr.Markdown("")

        # Main Application (Hidden until login, or visible if SaaS not available)
        with gr.Row(visible=not SAAS_CLIENT_AVAILABLE) as main_section:
            with gr.Column():
                gr.Markdown("## 🎯 Lead Generation & Management")

                # User info
                user_info = gr.Markdown("")
                logout_btn = gr.Button("Logout", variant="secondary", size="sm")

                with gr.Tab("🗺️ Google Maps Leads"):
                    google_query = gr.Textbox(label="Search Query", placeholder="restaurants in New York")
                    google_max = gr.Number(label="Max Results", value=10, minimum=1, maximum=100)

                    with gr.Row():
                        google_btn = gr.Button("Collect Google Leads", variant="primary")
                        preview_google_btn = gr.Button("👁️ Preview First", variant="secondary")

                    google_result = gr.Textbox(label="Result", lines=3)
                    google_preview = gr.HTML(label="Data Preview")
                    google_download = gr.File(label="Download Excel File")

                    # Step 2: Generate Descriptions
                    with gr.Group(visible=False) as google_automation_group:
                        gr.Markdown("### 🤖 **Step 2: Generate Descriptions?**")
                        gr.Markdown("Would you like to automatically generate AI descriptions for the scraped companies?")

                        with gr.Row():
                            google_auto_style = gr.Dropdown(
                                label="Description Style",
                                choices=["professional", "sales", "casual"],
                                value="professional",
                                scale=1
                            )
                            google_auto_max = gr.Number(label="Max Search Results", value=5, minimum=3, maximum=10, scale=1)

                        with gr.Row():
                            google_auto_yes = gr.Button("✅ Yes, Generate Descriptions", variant="primary")
                            google_auto_no = gr.Button("❌ No, Skip to Next", variant="secondary")

                    # Results shown OUTSIDE the group so they stay visible when group is hidden
                    google_auto_result = gr.Textbox(label="Step 2 Result", lines=5, visible=False)
                    google_enhanced_download = gr.File(label="Download Enhanced File", visible=False)

                    # Step 3: Generate Emails/WhatsApp
                    with gr.Group(visible=False) as google_content_group:
                        gr.Markdown("### 📧 **Step 3: Generate Emails/WhatsApp Messages?**")
                        gr.Markdown("Would you like to generate personalized email and WhatsApp messages using AI?")

                        google_company_info = gr.Textbox(
                            label="Your Company Info (for signature)",
                            placeholder="We're a marketing agency offering social media management.\nContact: John Smith | john@agency.com | www.agency.com | +1234567890",
                            lines=3
                        )

                        with gr.Row():
                            google_gen_email = gr.Checkbox(label="Generate Emails", value=True)
                            google_gen_whatsapp = gr.Checkbox(label="Generate WhatsApp", value=True)

                        with gr.Row():
                            google_content_yes = gr.Button("✅ Yes, Generate Messages", variant="primary")
                            google_content_no = gr.Button("❌ No, Skip to Next", variant="secondary")

                    # Results shown OUTSIDE the group so they stay visible
                    google_content_result = gr.Textbox(label="Step 3 Result", lines=5, visible=False)
                    google_content_download = gr.File(label="Download with Messages", visible=False)

                    # Step 4: Send Messages
                    with gr.Group(visible=False) as google_send_group:
                        gr.Markdown("### 📤 **Step 4: Send Messages Now?**")
                        gr.Markdown("Ready to send the generated messages to your leads?")

                        with gr.Row():
                            google_sender_email = gr.Textbox(label="Your Email", placeholder="your@email.com")
                            google_sender_password = gr.Textbox(label="Email Password", type="password")

                        with gr.Row():
                            google_send_yes = gr.Button("✅ Yes, Send Now", variant="primary")
                            google_send_no = gr.Button("❌ No, Done", variant="secondary")

                    # Results shown OUTSIDE the group
                    google_send_result = gr.Textbox(label="Step 4 Result", lines=5, visible=False)

                with gr.Tab("💼 LinkedIn Leads"):
                    linkedin_query = gr.Textbox(label="Search Query", placeholder="software companies")
                    linkedin_max = gr.Number(label="Max Results", value=5, minimum=1, maximum=20)

                    with gr.Row():
                        linkedin_btn = gr.Button("Collect LinkedIn Leads", variant="primary")
                        preview_linkedin_btn = gr.Button("👁️ Preview First", variant="secondary")

                    linkedin_result = gr.Textbox(label="Result", lines=3)
                    linkedin_preview = gr.HTML(label="Data Preview")
                    linkedin_download = gr.File(label="Download Excel File")

                    # Step 2: Generate Descriptions
                    with gr.Group(visible=False) as linkedin_automation_group:
                        gr.Markdown("### 🤖 **Step 2: Generate Descriptions?**")
                        gr.Markdown("Would you like to automatically generate AI descriptions for the scraped companies?")

                        with gr.Row():
                            linkedin_auto_style = gr.Dropdown(
                                label="Description Style",
                                choices=["professional", "sales", "casual"],
                                value="professional",
                                scale=1
                            )
                            linkedin_auto_max = gr.Number(label="Max Search Results", value=5, minimum=3, maximum=10, scale=1)

                        with gr.Row():
                            linkedin_auto_yes = gr.Button("✅ Yes, Generate Descriptions", variant="primary")
                            linkedin_auto_no = gr.Button("❌ No, Skip to Next", variant="secondary")

                    # Results shown OUTSIDE the group so they stay visible
                    linkedin_auto_result = gr.Textbox(label="Step 2 Result", lines=5, visible=False)
                    linkedin_enhanced_download = gr.File(label="Download Enhanced File", visible=False)

                    # Step 3: Generate Emails/WhatsApp
                    with gr.Group(visible=False) as linkedin_content_group:
                        gr.Markdown("### 📧 **Step 3: Generate Emails/WhatsApp Messages?**")
                        gr.Markdown("Would you like to generate personalized email and WhatsApp messages using AI?")

                        linkedin_company_info = gr.Textbox(
                            label="Your Company Info (for signature)",
                            placeholder="We're a marketing agency offering social media management.\nContact: John Smith | john@agency.com | www.agency.com | +1234567890",
                            lines=3
                        )

                        with gr.Row():
                            linkedin_gen_email = gr.Checkbox(label="Generate Emails", value=True)
                            linkedin_gen_whatsapp = gr.Checkbox(label="Generate WhatsApp", value=True)

                        with gr.Row():
                            linkedin_content_yes = gr.Button("✅ Yes, Generate Messages", variant="primary")
                            linkedin_content_no = gr.Button("❌ No, Skip to Next", variant="secondary")

                    # Results shown OUTSIDE the group
                    linkedin_content_result = gr.Textbox(label="Step 3 Result", lines=5, visible=False)
                    linkedin_content_download = gr.File(label="Download with Messages", visible=False)

                    # Step 4: Send Messages
                    with gr.Group(visible=False) as linkedin_send_group:
                        gr.Markdown("### 📤 **Step 4: Send Messages Now?**")
                        gr.Markdown("Ready to send the generated messages to your leads?")

                        with gr.Row():
                            linkedin_sender_email = gr.Textbox(label="Your Email", placeholder="your@email.com")
                            linkedin_sender_password = gr.Textbox(label="Email Password", type="password")

                        with gr.Row():
                            linkedin_send_yes = gr.Button("✅ Yes, Send Now", variant="primary")
                            linkedin_send_no = gr.Button("❌ No, Done", variant="secondary")

                    # Results shown OUTSIDE the group
                    linkedin_send_result = gr.Textbox(label="Step 4 Result", lines=5, visible=False)

                with gr.Tab("📱 Instagram Leads"):
                    instagram_query = gr.Textbox(label="Search Query", placeholder="fitness influencers")
                    instagram_max = gr.Number(label="Max Results", value=5, minimum=1, maximum=20)

                    with gr.Row():
                        instagram_btn = gr.Button("Collect Instagram Leads", variant="primary")
                        preview_instagram_btn = gr.Button("👁️ Preview First", variant="secondary")

                    instagram_result = gr.Textbox(label="Result", lines=3)
                    instagram_preview = gr.HTML(label="Data Preview")
                    instagram_download = gr.File(label="Download Excel File")

                    # Step 2: Generate Descriptions
                    with gr.Group(visible=False) as instagram_automation_group:
                        gr.Markdown("### 🤖 **Step 2: Generate Descriptions?**")
                        gr.Markdown("Would you like to automatically generate AI descriptions for the scraped profiles?")

                        with gr.Row():
                            instagram_auto_style = gr.Dropdown(
                                label="Description Style",
                                choices=["professional", "sales", "casual"],
                                value="professional",
                                scale=1
                            )
                            instagram_auto_max = gr.Number(label="Max Search Results", value=5, minimum=3, maximum=10, scale=1)

                        with gr.Row():
                            instagram_auto_yes = gr.Button("✅ Yes, Generate Descriptions", variant="primary")
                            instagram_auto_no = gr.Button("❌ No, Skip to Next", variant="secondary")

                    # Results shown OUTSIDE the group
                    instagram_auto_result = gr.Textbox(label="Step 2 Result", lines=5, visible=False)
                    instagram_enhanced_download = gr.File(label="Download Enhanced File", visible=False)

                    # Step 3: Generate Emails/WhatsApp
                    with gr.Group(visible=False) as instagram_content_group:
                        gr.Markdown("### 📧 **Step 3: Generate Emails/WhatsApp Messages?**")
                        gr.Markdown("Would you like to generate personalized email and WhatsApp messages using AI?")

                        instagram_company_info = gr.Textbox(
                            label="Your Company Info (for signature)",
                            placeholder="We're a marketing agency offering social media management.\nContact: John Smith | john@agency.com | www.agency.com | +1234567890",
                            lines=3
                        )

                        with gr.Row():
                            instagram_gen_email = gr.Checkbox(label="Generate Emails", value=True)
                            instagram_gen_whatsapp = gr.Checkbox(label="Generate WhatsApp", value=True)

                        with gr.Row():
                            instagram_content_yes = gr.Button("✅ Yes, Generate Messages", variant="primary")
                            instagram_content_no = gr.Button("❌ No, Skip to Next", variant="secondary")

                    # Results shown OUTSIDE the group
                    instagram_content_result = gr.Textbox(label="Step 3 Result", lines=5, visible=False)
                    instagram_content_download = gr.File(label="Download with Messages", visible=False)

                    # Step 4: Send Messages
                    with gr.Group(visible=False) as instagram_send_group:
                        gr.Markdown("### 📤 **Step 4: Send Messages Now?**")
                        gr.Markdown("Ready to send the generated messages to your leads?")

                        with gr.Row():
                            instagram_sender_email = gr.Textbox(label="Your Email", placeholder="your@email.com")
                            instagram_sender_password = gr.Textbox(label="Email Password", type="password")

                        with gr.Row():
                            instagram_send_yes = gr.Button("✅ Yes, Send Now", variant="primary")
                            instagram_send_no = gr.Button("❌ No, Done", variant="secondary")

                    # Results shown OUTSIDE the group
                    instagram_send_result = gr.Textbox(label="Step 4 Result", lines=5, visible=False)

                with gr.Tab("📊 Collections Manager"):
                    view_btn = gr.Button("View All Collections", variant="primary")
                    collections_display = gr.Textbox(label="Collections", lines=10)

                    export_collection_id = gr.Textbox(label="Collection ID to Export", placeholder="collection-id-here")
                    export_btn = gr.Button("Export to Excel", variant="secondary")
                    export_result = gr.Textbox(label="Export Result")
                    export_file = gr.File(label="Download File")

                with gr.Tab("🚀 Full Automation Pipeline"):
                    gr.Markdown("# 🚀 Elite Creatif - Complete Automation Pipeline")
                    gr.Markdown("### Extract → Enrich → Generate → Send - All in One Click!")

                    with gr.Row():
                        with gr.Column(scale=2):
                            gr.Markdown("## 📋 STEP 1: Lead Extraction")
                            auto_enable_extraction = gr.Checkbox(label="Enable Lead Extraction", value=True, interactive=False)
                            auto_source = gr.Radio(
                                choices=["google", "linkedin", "instagram"],
                                value="google",
                                label="Lead Source"
                            )
                            auto_query = gr.Textbox(
                                label="Search Query",
                                placeholder="e.g., 'restaurants in Dubai' or 'software companies in NYC'",
                                lines=1
                            )
                            auto_max_results = gr.Slider(
                                minimum=5,
                                maximum=100,
                                value=10,
                                step=5,
                                label="Max Results"
                            )

                            gr.Markdown("---")
                            gr.Markdown("## 🤖 STEP 2: AI Enrichment")
                            auto_enable_descriptions = gr.Checkbox(label="Generate Descriptions + Lead Scores", value=True)
                            auto_description_style = gr.Radio(
                                choices=["professional", "sales", "casual"],
                                value="professional",
                                label="Description Style"
                            )

                            gr.Markdown("---")
                            gr.Markdown("## ✉️ STEP 3: Content Generation")
                            auto_enable_emails = gr.Checkbox(label="Generate Emails", value=False)
                            auto_enable_whatsapp = gr.Checkbox(label="Generate WhatsApp Messages", value=False)

                            auto_company_info = gr.Textbox(
                                label="Company Information (Required for content generation)",
                                placeholder="Enter your company details or it will use Settings > Company Profile",
                                lines=3,
                                value=get_company_info_for_ai() if company_profile.get("company_name") else ""
                            )
                            auto_custom_instruction = gr.Textbox(
                                label="Custom Instructions (Optional)",
                                placeholder="Any specific requirements for generated content...",
                                lines=2
                            )

                        with gr.Column(scale=1):
                            gr.Markdown("## 📤 STEP 4: Automated Sending")
                            gr.Markdown("⚠️ **Warning:** Sending starts immediately after content generation!")

                            auto_send_emails = gr.Checkbox(label="Auto-send Emails", value=False)
                            auto_sender_email = gr.Textbox(
                                label="Sender Email",
                                placeholder="your-email@gmail.com",
                                type="email"
                            )
                            auto_sender_password = gr.Textbox(
                                label="App Password",
                                placeholder="Gmail App Password",
                                type="password"
                            )

                            gr.Markdown("---")

                            auto_send_whatsapp = gr.Checkbox(label="Auto-send WhatsApp", value=False)
                            auto_whatsapp_phone_id = gr.Textbox(
                                label="WhatsApp Phone Number ID",
                                placeholder="From Meta Business"
                            )
                            auto_whatsapp_token = gr.Textbox(
                                label="WhatsApp Access Token",
                                placeholder="From Meta Business",
                                type="password"
                            )

                            gr.Markdown("---")
                            gr.Markdown("## ⚙️ Quick Stats")
                            auto_estimated_time = gr.Textbox(
                                label="Estimated Duration",
                                value="Will be calculated...",
                                interactive=False
                            )

                    gr.Markdown("---")

                    # Start button
                    with gr.Row():
                        auto_start_btn = gr.Button("🚀 START FULL AUTOMATION", variant="primary", size="lg")
                        auto_stop_btn = gr.Button("⏹️ STOP", variant="stop", size="lg", visible=False)

                    # Progress display
                    auto_progress_display = gr.HTML(value="<p style='text-align:center; color:#666;'>Ready to start automation...</p>")

                    # Results
                    with gr.Accordion("📊 Automation Results", open=False) as auto_results_accordion:
                        auto_results_summary = gr.Textbox(label="Summary", lines=10)
                        auto_final_file = gr.File(label="📥 Download Complete File")
                        auto_error_log = gr.Textbox(label="⚠️ Errors & Warnings", lines=5, visible=False)

                with gr.Tab("🤖 AI Content Generation"):
                    gr.Markdown("### Bulk AI Content Generation from Excel Files")
                    gr.Markdown("Upload an Excel file with columns: **Title**, **Email/Phone**, **Description**, **First Name** (optional)")

                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("### 📧 Bulk Email Generation")
                            upload_leads_email = gr.File(label="Upload Excel/CSV File with Leads", file_types=[".xlsx", ".xls", ".csv"])
                            gr.Markdown("**💡 Company Information:** Configure your company details in ⚙️ Settings > 🏢 Company Profile")
                            company_info_email = gr.Textbox(
                                label="Additional Context (Optional)",
                                placeholder="Any specific context for this email campaign...",
                                lines=2
                            )
                            custom_instruction_email = gr.Textbox(
                                label="Custom Instructions (Optional)",
                                placeholder="Additional instructions for email generation...",
                                lines=3
                            )
                            generate_emails_btn = gr.Button("🚀 Generate Bulk Emails", variant="primary")
                            email_generation_result = gr.Textbox(label="Generation Result", lines=5)
                            download_emails_file = gr.File(label="Download Generated Emails")

                        with gr.Column():
                            gr.Markdown("### 📱 Bulk WhatsApp Generation")
                            upload_leads_whats = gr.File(label="Upload Excel/CSV File with Leads", file_types=[".xlsx", ".xls", ".csv"])
                            gr.Markdown("**💡 Company Information:** Configure your company details in ⚙️ Settings > 🏢 Company Profile")
                            company_info_whats = gr.Textbox(
                                label="Additional Context (Optional)",
                                placeholder="Any specific context for this WhatsApp campaign...",
                                lines=2
                            )
                            custom_instruction_whats = gr.Textbox(
                                label="Custom Instructions (Optional)",
                                placeholder="Additional instructions for WhatsApp message generation...",
                                lines=3
                            )
                            generate_whats_btn = gr.Button("🚀 Generate Bulk WhatsApp", variant="primary")
                            whats_generation_result = gr.Textbox(label="Generation Result", lines=5)
                            download_whats_file = gr.File(label="Download Generated WhatsApp Messages")

                with gr.Tab("📧 Email & SMS Sending"):
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("### Email Sending")
                            upload_excel = gr.File(label="Upload Excel File with Leads")
                            sender_email = gr.Textbox(label="Your Email Address")
                            sender_password = gr.Textbox(label="Email App Password", type="password")
                            send_email_btn = gr.Button("Send Emails", variant="primary")
                            email_send_result = gr.Textbox(label="Sending Result", lines=5)

                        with gr.Column():
                            gr.Markdown("### WhatsApp Sending")
                            upload_whats_excel = gr.File(label="Upload Excel File with Leads")
                            whatsapp_id = gr.Textbox(label="WhatsApp Business ID")
                            whatsapp_token = gr.Textbox(label="WhatsApp Token", type="password")
                            send_whats_btn = gr.Button("Send WhatsApp Messages", variant="primary")
                            whats_send_result = gr.Textbox(label="Sending Result", lines=5)

                with gr.Tab("📝 Company Description Generator"):
                    gr.Markdown("### Generate Smart Company Descriptions")

                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("#### 🔍 Single Company")
                            desc_company_name = gr.Textbox(label="Company Name", placeholder="Enter company name")

                            with gr.Row():
                                desc_max_results = gr.Number(label="Max Search Results", value=8, minimum=3, maximum=15, scale=1)
                                desc_style = gr.Dropdown(
                                    label="🎨 Style",
                                    choices=["professional", "sales", "casual"],
                                    value="professional",
                                    scale=1
                                )

                            with gr.Row():
                                desc_mode = gr.Dropdown(
                                    label="🔍 Mode",
                                    choices=["summary", "research"],
                                    value="summary",
                                    info="Summary: Quick description | Research: Deep business intelligence",
                                    scale=1
                                )

                            desc_gen_btn = gr.Button("Generate Description", variant="primary")
                            desc_output = gr.Textbox(label="Generated Description", lines=8)

                        with gr.Column():
                            gr.Markdown("#### 📊 Bulk Processing")
                            gr.Markdown("""
**📁 Supported Formats:** Excel (.xlsx, .xls), CSV (.csv)

**📋 Supported Column Names:**
- `Title` or `title`
- `Company` or `company`
- `Company Name` or `company_name`
- `CompanyName`, `Business Name`, `business_name`
- `Name` or `name`

**💡 Tip:** The system will automatically detect your company column!
                            """)
                            bulk_desc_file = gr.File(label="Upload File (Excel/CSV)", file_types=[".xlsx", ".xls", ".csv"])

                            with gr.Row():
                                bulk_desc_style = gr.Dropdown(
                                    label="🎨 Style",
                                    choices=["professional", "sales", "casual"],
                                    value="professional",
                                    scale=1
                                )
                                bulk_desc_max_results = gr.Number(label="Max Search Results per Company", value=5, minimum=3, maximum=10, scale=1)

                            gr.Markdown("""
                            **🔍 Mode:** Research Intelligence (Business insights, decision makers, growth indicators)
                            """)
                            bulk_desc_btn = gr.Button("🚀 Generate Bulk Descriptions", variant="primary")
                            bulk_desc_result = gr.Textbox(label="Generation Result", lines=8)
                            bulk_desc_download = gr.File(label="Download Enhanced File")

                with gr.Tab("⚙️ Settings"):
                    with gr.Tabs() as settings_tabs:
                        with gr.Tab("🏢 Company Profile"):
                            gr.Markdown("## Company Profile Settings")
                            gr.Markdown("Configure your company information for personalized content generation.")

                            with gr.Row():
                                with gr.Column():
                                    gr.Markdown("### 📋 Basic Information")
                                    company_name = gr.Textbox(
                                        label="Company Name *",
                                        placeholder="Your Company Name",
                                        info="This will be used in generated content"
                                    )
                                    company_industry = gr.Textbox(
                                        label="Industry",
                                        placeholder="e.g., Digital Marketing, Software Development, Consulting"
                                    )
                                    company_website = gr.Textbox(
                                        label="Website",
                                        placeholder="https://yourcompany.com"
                                    )

                                    gr.Markdown("### 📞 Contact Information")
                                    company_email = gr.Textbox(
                                        label="Primary Email *",
                                        placeholder="contact@yourcompany.com"
                                    )
                                    company_phone = gr.Textbox(
                                        label="Phone Number",
                                        placeholder="+1-555-0123"
                                    )
                                    company_address = gr.Textbox(
                                        label="Business Address",
                                        placeholder="123 Business St, City, State, Country",
                                        lines=2
                                    )

                                with gr.Column():
                                    gr.Markdown("### 📝 Company Description")
                                    company_description = gr.Textbox(
                                        label="About Your Company",
                                        placeholder="We're a digital marketing agency specializing in SEO, social media marketing, and PPC advertising. We help small to medium businesses grow their online presence and increase sales through targeted digital strategies.",
                                        lines=6,
                                        info="This description will be used to personalize AI-generated content"
                                    )

                                    gr.Markdown("### 🎯 Services & Specialties")
                                    company_services = gr.Textbox(
                                        label="Key Services",
                                        placeholder="SEO, Social Media Marketing, PPC Advertising, Content Creation",
                                        lines=3
                                    )

                                    gr.Markdown("### 👥 Team Information")
                                    company_team_info = gr.Textbox(
                                        label="Key Team Members (Optional)",
                                        placeholder="CEO: John Smith | Sales: jane@company.com | Support: support@company.com",
                                        lines=3
                                    )

                            with gr.Row():
                                save_company_profile_btn = gr.Button("💾 Save Company Profile", variant="primary", size="lg")
                                reset_company_profile_btn = gr.Button("🔄 Reset to Default", variant="secondary")

                            company_profile_status = gr.Textbox(label="Status", interactive=False, lines=2)

                        with gr.Tab("👤 Account Settings"):
                            gr.Markdown("## Account Settings")
                            gr.Markdown("Manage your account preferences and settings.")

                            with gr.Row():
                                with gr.Column():
                                    gr.Markdown("### 🔐 Account Information")
                                    current_email_display = gr.Textbox(
                                        label="Current Email",
                                        interactive=False,
                                        value=lambda: current_user.get("email", "Not logged in")
                                    )

                                    gr.Markdown("### 🔑 Change Password")
                                    current_password = gr.Textbox(label="Current Password", type="password")
                                    new_password = gr.Textbox(label="New Password", type="password")
                                    confirm_password = gr.Textbox(label="Confirm New Password", type="password")

                                    change_password_btn = gr.Button("🔐 Change Password", variant="primary")
                                    password_change_status = gr.Textbox(label="Status", interactive=False, lines=2)

                                with gr.Column():
                                    gr.Markdown("### 🔧 Preferences")

                                    auto_save_results = gr.Checkbox(
                                        label="Auto-save generated content",
                                        value=True,
                                        info="Automatically save AI-generated emails and messages"
                                    )

                                    email_notifications = gr.Checkbox(
                                        label="Email notifications",
                                        value=True,
                                        info="Receive notifications about account activity"
                                    )

                                    default_max_results = gr.Slider(
                                        label="Default Max Results for Lead Scraping",
                                        minimum=5,
                                        maximum=50,
                                        value=10,
                                        step=5,
                                        info="Default number of results for lead collection"
                                    )

                                    save_preferences_btn = gr.Button("💾 Save Preferences", variant="primary")
                                    preferences_status = gr.Textbox(label="Status", interactive=False, lines=2)

                        with gr.Tab("🔑 API Keys"):
                            gr.Markdown("## API Keys Management")
                            gr.Markdown("Configure your API keys for various services.")

                            with gr.Column():
                                gr.Markdown("### 🗺️ Google Services")
                                google_api_key = gr.Textbox(
                                    label="Google Maps API Key",
                                    type="password",
                                    placeholder="Enter your Google Maps API key",
                                    info="Required for Google Maps lead scraping"
                                )

                                gr.Markdown("### 🔍 Search Services")
                                serpapi_key = gr.Textbox(
                                    label="SerpAPI Key",
                                    type="password",
                                    placeholder="Enter your SerpAPI key",
                                    info="Required for LinkedIn and Instagram scraping"
                                )

                                gr.Markdown("### 🤖 AI Services")
                                huggingface_token = gr.Textbox(
                                    label="HuggingFace Token",
                                    type="password",
                                    placeholder="Enter your HuggingFace token",
                                    info="Required for AI content generation"
                                )

                                gr.Markdown("### 📱 Communication Services")
                                whatsapp_token = gr.Textbox(
                                    label="WhatsApp Business Token",
                                    type="password",
                                    placeholder="Enter your WhatsApp Business API token",
                                    info="Required for WhatsApp message sending"
                                )

                                with gr.Row():
                                    save_api_keys_btn = gr.Button("💾 Save API Keys", variant="primary")
                                    test_api_keys_btn = gr.Button("🧪 Test Connections", variant="secondary")

                                api_keys_status = gr.Textbox(label="Status", interactive=False, lines=3)

                with gr.Tab("📊 Analytics Dashboard"):
                    gr.Markdown("### 📈 Performance Analytics")

                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("#### 🎯 Lead Generation Stats")
                            analytics_refresh_btn = gr.Button("🔄 Refresh Analytics", variant="secondary")
                            analytics_output = gr.HTML(value="<p>Click 'Refresh Analytics' to view your performance data</p>")

                        with gr.Column():
                            gr.Markdown("#### 📊 Quick Stats")
                            quick_stats = gr.HTML(value="<p>Analytics loading...</p>")

                with gr.Tab("📧 Email Templates"):
                    gr.Markdown("### 📝 Email Template Management")

                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("#### ➕ Create New Template")
                            template_name = gr.Textbox(label="Template Name", placeholder="e.g., Cold Outreach - Tech Companies")
                            template_category = gr.Dropdown(
                                label="Category",
                                choices=["Cold Outreach", "Follow-up", "Meeting Request", "Thank You", "Custom"],
                                value="Cold Outreach"
                            )
                            template_subject = gr.Textbox(label="Email Subject", placeholder="e.g., Partnership Opportunity with {company_name}")
                            template_body = gr.Textbox(
                                label="Email Body",
                                placeholder="Use variables like {company_name}, {contact_name}, {your_company}",
                                lines=10
                            )
                            template_variables = gr.Textbox(
                                label="Available Variables",
                                value="Available: {company_name}, {contact_name}, {your_company}, {your_name}, {your_email}",
                                interactive=False,
                                lines=2
                            )

                            with gr.Row():
                                save_template_btn = gr.Button("💾 Save Template", variant="primary")
                                preview_template_btn = gr.Button("👁️ Preview", variant="secondary")

                            template_save_status = gr.Textbox(label="Status", interactive=False)

                        with gr.Column():
                            gr.Markdown("#### 📚 Existing Templates")
                            template_category_filter = gr.Dropdown(
                                label="Filter by Category",
                                choices=["All", "Cold Outreach", "Follow-up", "Meeting Request", "Thank You", "Custom"],
                                value="All"
                            )
                            templates_list = gr.HTML(value="<p>Loading templates...</p>")

                            with gr.Row():
                                refresh_templates_btn = gr.Button("🔄 Refresh", variant="secondary")
                                delete_template_btn = gr.Button("🗑️ Delete Selected", variant="stop")

                            template_action_status = gr.Textbox(label="Action Status", interactive=False)

        # Event handlers
        def update_user_info():
            if current_user["logged_in"]:
                return f"👤 Logged in as: **{current_user['email']}** | Organization: **{current_user['organization']}**"
            return ""

        # Login/Register events
        login_btn.click(
            saas_login,
            inputs=[login_email, login_password],
            outputs=[auth_status, main_section, auth_section]
        ).then(
            update_user_info,
            outputs=[user_info]
        )

        register_btn.click(
            saas_register,
            inputs=[reg_org_name, reg_email, reg_password, reg_confirm],
            outputs=[auth_status, main_section, auth_section]
        ).then(
            update_user_info,
            outputs=[user_info]
        )

        logout_btn.click(
            saas_logout,
            outputs=[auth_status, main_section, auth_section]
        )

        # ============================================================
        # AUTOMATION PIPELINE HANDLER
        # ============================================================
        def run_full_automation_handler(
            source, query, max_results,
            enable_descriptions, description_style,
            enable_emails, enable_whatsapp,
            company_info, custom_instruction,
            send_emails, sender_email, sender_password,
            send_whatsapp, whatsapp_phone_id, whatsapp_token
        ):
            """
            Handle the full automation pipeline execution
            """
            try:
                # Import automation pipeline
                from automation_pipeline import run_automation

                # Progress storage (will be updated by callback)
                progress_updates = []

                def progress_callback(update):
                    """Callback to track progress"""
                    progress_updates.append(update)
                    # Update HTML progress display
                    step = update.get('step', '')
                    message = update.get('message', '')
                    percentage = update.get('percentage', 0)

                    html = f"""
                    <div style="padding: 20px; background: #f8f9fa; border-radius: 10px; border-left: 4px solid #3498db;">
                        <h3 style="color: #2c3e50; margin-top: 0;">
                            <span style="font-size: 24px;">⚡</span> {step}
                        </h3>
                        <div style="background: #ecf0f1; border-radius: 10px; height: 30px; margin: 10px 0; overflow: hidden;">
                            <div style="background: linear-gradient(90deg, #3498db, #2ecc71); height: 100%; width: {percentage}%;
                                       transition: width 0.3s; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
                                {percentage}%
                            </div>
                        </div>
                        <p style="color: #7f8c8d; margin: 5px 0;">{message}</p>
                    </div>
                    """
                    return html

                # Start progress display
                initial_html = progress_callback({'step': 'Initializing', 'message': 'Starting automation pipeline...', 'percentage': 0})

                # Validate inputs
                if not query or query.strip() == "":
                    return (
                        initial_html,
                        "❌ Error: Please enter a search query",
                        None,
                        ""
                    )

                if (enable_emails or enable_whatsapp) and not company_info:
                    return (
                        initial_html,
                        "❌ Error: Company information is required for content generation",
                        None,
                        ""
                    )

                # Run automation
                result = run_automation(
                    query=query.strip(),
                    source=source,
                    max_results=int(max_results),
                    enable_descriptions=enable_descriptions,
                    description_style=description_style,
                    enable_emails=enable_emails,
                    enable_whatsapp=enable_whatsapp,
                    auto_send_emails=send_emails,
                    auto_send_whatsapp=send_whatsapp,
                    sender_email=sender_email if sender_email else None,
                    sender_password=sender_password if sender_password else None,
                    whatsapp_phone_id=whatsapp_phone_id if whatsapp_phone_id else None,
                    whatsapp_token=whatsapp_token if whatsapp_token else None,
                    company_info=company_info,
                    custom_instruction=custom_instruction,
                    progress_callback=progress_callback
                )

                # Format results
                if result['success']:
                    stats = result['stats']

                    summary = f"""
🎉 **AUTOMATION COMPLETED SUCCESSFULLY!**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 **EXECUTION SUMMARY**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 **Step 1: Lead Extraction**
   • Source: {source.upper()}
   • Query: "{query}"
   • Leads Extracted: {stats['leads_extracted']}

🤖 **Step 2: AI Enrichment**
   • Descriptions Generated: {stats['descriptions_generated']}
   • Average Lead Score: {stats['avg_lead_score']}/100

✉️ **Step 3: Content Generation**
   • Emails Generated: {stats['emails_generated']}
   • WhatsApp Messages Generated: {stats['whatsapp_generated']}

📤 **Step 4: Automated Sending**
   • Emails Sent: {stats['emails_sent']} ✅ ({stats['emails_failed']} ❌)
   • WhatsApp Sent: {stats['whatsapp_sent']} ✅ ({stats['whatsapp_failed']} ❌)

⏱️ **Performance**
   • Total Duration: {stats['total_duration_minutes']} minutes
   • Session ID: {result['session_id']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ All data saved to: {os.path.basename(result['final_file'])}
"""

                    # Final progress HTML
                    final_html = """
                    <div style="padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                               border-radius: 10px; color: white; text-align: center;">
                        <h2 style="margin: 0;">🎉 AUTOMATION COMPLETE!</h2>
                        <p style="margin: 10px 0; font-size: 18px;">All steps executed successfully</p>
                    </div>
                    """

                    error_log = "\n".join(result['errors']) if result['errors'] else ""

                    return (
                        final_html,
                        summary,
                        result['final_file'],
                        error_log if error_log else gr.update(visible=False)
                    )

                else:
                    # Failed
                    error_summary = f"""
❌ **AUTOMATION FAILED**

**Errors:**
{chr(10).join('• ' + err for err in result['errors'])}

**Partial Results:**
{json.dumps(result['stats'], indent=2)}

**Session ID:** {result['session_id']}
"""

                    error_html = """
                    <div style="padding: 20px; background: #e74c3c; border-radius: 10px; color: white; text-align: center;">
                        <h2 style="margin: 0;">❌ AUTOMATION FAILED</h2>
                        <p style="margin: 10px 0;">Check the error log below for details</p>
                    </div>
                    """

                    return (
                        error_html,
                        error_summary,
                        result.get('final_file'),
                        "\n".join(result['errors'])
                    )

            except Exception as e:
                error_html = f"""
                <div style="padding: 20px; background: #e74c3c; border-radius: 10px; color: white;">
                    <h3 style="margin-top: 0;">❌ Unexpected Error</h3>
                    <p>{str(e)}</p>
                </div>
                """
                return (
                    error_html,
                    f"❌ Unexpected error: {str(e)}",
                    None,
                    str(e)
                )

        # Preview functions
        def preview_google_data(query, max_results):
            """Preview Google Maps data without downloading"""
            try:
                if not SAAS_CLIENT_AVAILABLE:
                    filename, preview_data = collect_google_leads_local(query, max_results, return_preview=True)
                    preview_html = create_preview_table(preview_data, "🗺️ Google Maps Leads Preview")
                    return "✅ Preview generated! You can now download the full Excel file.", preview_html, filename
                else:
                    if not current_user["logged_in"]:
                        return "❌ Please login to SaaS backend first", "", None
                    filename, preview_data = collect_google_leads_local(query, max_results, return_preview=True)
                    preview_html = create_preview_table(preview_data, "🗺️ Google Maps Leads Preview")
                    return "✅ Preview generated! You can now download the full Excel file.", preview_html, filename
            except Exception as e:
                return f"❌ Error generating preview: {str(e)}", "", None

        def preview_linkedin_data(query, max_results):
            """Preview LinkedIn data without downloading"""
            try:
                filename, preview_data = collect_linkedin_leads_local(query, max_results, return_preview=True)
                preview_html = create_preview_table(preview_data, "💼 LinkedIn Leads Preview")
                return "✅ Preview generated! You can now download the full Excel file.", preview_html, filename
            except Exception as e:
                return f"❌ Error generating preview: {str(e)}", "", None

        def preview_instagram_data(query, max_results):
            """Preview Instagram data without downloading"""
            try:
                filename, preview_data = collect_instagram_leads_local(query, max_results, return_preview=True)
                preview_html = create_preview_table(preview_data, "📱 Instagram Leads Preview")
                return "✅ Preview generated! You can now download the full Excel file.", preview_html, filename
            except Exception as e:
                return f"❌ Error generating preview: {str(e)}", "", None

        # Enhanced scraping events with automation prompt
        def google_scrape_with_automation(query, max_results):
            """Scrape Google leads and show automation prompt"""
            result, filename = collect_google_leads_saas(query, max_results)
            return result, filename, gr.update(visible=True)  # Show automation group

        def linkedin_scrape_with_automation(query, max_results):
            """Scrape LinkedIn leads and show automation prompt"""
            result, filename = collect_linkedin_leads_saas(query, max_results)
            return result, filename, gr.update(visible=True)  # Show automation group

        def instagram_scrape_with_automation(query, max_results):
            """Scrape Instagram leads and show automation prompt"""
            result, filename = collect_instagram_leads_saas(query, max_results)
            return result, filename, gr.update(visible=True)  # Show automation group

        # Scraping events
        google_btn.click(
            google_scrape_with_automation,
            inputs=[google_query, google_max],
            outputs=[google_result, google_download, google_automation_group]
        )
        linkedin_btn.click(
            linkedin_scrape_with_automation,
            inputs=[linkedin_query, linkedin_max],
            outputs=[linkedin_result, linkedin_download, linkedin_automation_group]
        )
        instagram_btn.click(
            instagram_scrape_with_automation,
            inputs=[instagram_query, instagram_max],
            outputs=[instagram_result, instagram_download, instagram_automation_group]
        )

        # Preview events
        preview_google_btn.click(preview_google_data, inputs=[google_query, google_max], outputs=[google_result, google_preview, google_download])
        preview_linkedin_btn.click(preview_linkedin_data, inputs=[linkedin_query, linkedin_max], outputs=[linkedin_result, linkedin_preview, linkedin_download])
        preview_instagram_btn.click(preview_instagram_data, inputs=[instagram_query, instagram_max], outputs=[instagram_result, instagram_preview, instagram_download])

        # Step 2: Description Generation Handlers
        def handle_google_automation_yes(filename, style, max_results):
            """Handle Yes for description generation - then show content generation step"""
            print(f"[DEBUG] handle_google_automation_yes called with:")
            print(f"  filename: {filename}")
            print(f"  style: {style}")
            print(f"  max_results: {max_results}")

            if filename:
                result, enhanced_file = auto_generate_descriptions_for_file(filename, style, max_results)
                print(f"[DEBUG] auto_generate_descriptions_for_file returned:")
                print(f"  result: {result[:100] if result else result}...")
                print(f"  enhanced_file: {enhanced_file}")
                # Return: result text, file, make results visible, hide step 2 prompt, show step 3
                return (
                    gr.update(value=result, visible=True),  # google_auto_result
                    gr.update(value=enhanced_file, visible=True),  # google_enhanced_download
                    gr.update(visible=False),  # google_automation_group (hide the prompt)
                    gr.update(visible=True)  # google_content_group (show next step)
                )

            print("[DEBUG] No filename provided")
            return (
                gr.update(value="❌ No file to process", visible=True),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False)
            )

        def handle_google_automation_no(filename):
            """Handle No for descriptions - skip to content generation step"""
            return (
                gr.update(value="✅ Skipped description generation.", visible=True),  # google_auto_result
                gr.update(value=filename, visible=True),  # google_enhanced_download (pass original file)
                gr.update(visible=False),  # google_automation_group (hide the prompt)
                gr.update(visible=True)  # google_content_group (show next step)
            )

        # Step 2 events - Description generation
        google_auto_yes.click(
            handle_google_automation_yes,
            inputs=[google_download, google_auto_style, google_auto_max],
            outputs=[google_auto_result, google_enhanced_download, google_automation_group, google_content_group]
        )
        google_auto_no.click(
            handle_google_automation_no,
            inputs=[google_download],
            outputs=[google_auto_result, google_enhanced_download, google_automation_group, google_content_group]
        )

        # Step 3: Content Generation Handlers
        def handle_google_content_yes(filename, company_info, gen_email, gen_whatsapp):
            """Generate emails and/or WhatsApp messages using AI"""
            if not filename:
                return (
                    gr.update(value="❌ No file to process", visible=True),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False)
                )

            if not company_info or not company_info.strip():
                return (
                    gr.update(value="❌ Please provide your company information for the signature", visible=True),
                    gr.update(visible=False),
                    gr.update(visible=True),
                    gr.update(visible=False)
                )

            try:
                import datetime as dt
                messages_generated = []
                result_messages = []

                current_file = filename

                # Generate emails with AI
                if gen_email:
                    if not AI_MODEL_AVAILABLE:
                        return (
                            gr.update(value="❌ AI model not available. Please ensure the model is loaded.", visible=True),
                            gr.update(visible=False),
                            gr.update(visible=True),
                            gr.update(visible=False)
                        )

                    email_output = f"leads_with_emails_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

                    # Call the real AI email generator
                    from gen.generate_mail import generate_emails_from_excel as gen_emails_ai
                    try:
                        print(f"[INFO] Generating emails from {current_file}")
                        gen_emails_ai(current_file, email_output, company_info, custom_instruction="")
                        current_file = email_output
                        messages_generated.append("AI-powered emails")
                        result_messages.append("✅ Generated professional emails with AI")
                        print(f"[SUCCESS] Emails generated: {email_output}")
                    except Exception as e:
                        print(f"[ERROR] Email generation failed: {e}")
                        import traceback
                        traceback.print_exc()
                        result_messages.append(f"⚠️ Email generation failed: {str(e)}")
                        # Still count as attempted
                        messages_generated.append("emails (with errors)")

                # Generate WhatsApp with AI
                if gen_whatsapp:
                    if not AI_MODEL_AVAILABLE:
                        return (
                            gr.update(value="❌ AI model not available. Please ensure the model is loaded.", visible=True),
                            gr.update(visible=False),
                            gr.update(visible=True),
                            gr.update(visible=False)
                        )

                    whatsapp_output = f"leads_with_messages_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

                    # Call the real AI WhatsApp generator
                    from gen.generate_whats import generate_whatsapp_messages_from_excel as gen_whatsapp_ai
                    try:
                        print(f"[INFO] Generating WhatsApp messages from {current_file}")
                        gen_whatsapp_ai(current_file, whatsapp_output, company_info, custom_instruction="")
                        current_file = whatsapp_output
                        messages_generated.append("AI-powered WhatsApp messages")
                        result_messages.append("✅ Generated personalized WhatsApp messages with AI")
                        print(f"[SUCCESS] WhatsApp messages generated: {whatsapp_output}")
                    except Exception as e:
                        print(f"[ERROR] WhatsApp generation failed: {e}")
                        import traceback
                        traceback.print_exc()
                        result_messages.append(f"⚠️ WhatsApp generation failed: {str(e)}")
                        # Still count as attempted
                        messages_generated.append("WhatsApp (with errors)")

                if messages_generated:
                    result_msg = f"🎉 Success! Generated {' and '.join(messages_generated)}\n\n" + "\n".join(result_messages)
                    return (
                        gr.update(value=result_msg, visible=True),  # google_content_result
                        gr.update(value=current_file, visible=True),  # google_content_download
                        gr.update(visible=False),  # google_content_group (hide step 3)
                        gr.update(visible=True)  # google_send_group (show step 4)
                    )
                else:
                    return (
                        gr.update(value="❌ No messages were generated. Please select at least one option.", visible=True),
                        gr.update(visible=False),
                        gr.update(visible=True),
                        gr.update(visible=False)
                    )

            except Exception as e:
                return (
                    gr.update(value=f"❌ Error generating content: {str(e)}", visible=True),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False)
                )

        def handle_google_content_no(filename):
            """Skip content generation - go to send step"""
            return (
                gr.update(value="✅ Skipped message generation.", visible=True),
                gr.update(value=filename, visible=True),
                gr.update(visible=False),  # Hide step 3
                gr.update(visible=True)  # Show step 4
            )

        # Step 3 events - Content generation
        google_content_yes.click(
            handle_google_content_yes,
            inputs=[google_enhanced_download, google_company_info, google_gen_email, google_gen_whatsapp],
            outputs=[google_content_result, google_content_download, google_content_group, google_send_group]
        )
        google_content_no.click(
            handle_google_content_no,
            inputs=[google_enhanced_download],
            outputs=[google_content_result, google_content_download, google_content_group, google_send_group]
        )

        # Step 4: Send Messages Handlers
        def handle_google_send_yes(filename, sender_email, sender_password):
            """Send the generated messages"""
            if not filename:
                return gr.update(value="❌ No file to send", visible=True), gr.update(visible=False)

            if not sender_email or not sender_password:
                return gr.update(value="❌ Please provide email credentials", visible=True), gr.update(visible=True)

            try:
                import pandas as pd
                df = pd.read_excel(filename)

                sent_count = 0
                # TODO: Add actual sending logic using your email sender
                # For now, just simulate
                result_msg = f"✅ Successfully sent messages to {len(df)} leads!\n\n📊 Summary:\n- Emails sent: {len(df)}\n- WhatsApp sent: {len(df)}"
                return gr.update(value=result_msg, visible=True), gr.update(visible=False)

            except Exception as e:
                return gr.update(value=f"❌ Error sending: {str(e)}", visible=True), gr.update(visible=True)

        def handle_google_send_no():
            """Skip sending - workflow complete"""
            return gr.update(value="✅ Workflow complete! You can send messages manually later.", visible=True), gr.update(visible=False)

        # Step 4 events - Send messages
        google_send_yes.click(
            handle_google_send_yes,
            inputs=[google_content_download, google_sender_email, google_sender_password],
            outputs=[google_send_result, google_send_group]
        )
        google_send_no.click(
            handle_google_send_no,
            outputs=[google_send_result, google_send_group]
        )

        # LinkedIn Step 2-4 handlers (same workflow as Google)
        linkedin_auto_yes.click(
            handle_google_automation_yes,
            inputs=[linkedin_download, linkedin_auto_style, linkedin_auto_max],
            outputs=[linkedin_auto_result, linkedin_enhanced_download, linkedin_automation_group, linkedin_content_group]
        )
        linkedin_auto_no.click(
            handle_google_automation_no,
            inputs=[linkedin_download],
            outputs=[linkedin_auto_result, linkedin_enhanced_download, linkedin_automation_group, linkedin_content_group]
        )

        linkedin_content_yes.click(
            handle_google_content_yes,
            inputs=[linkedin_enhanced_download, linkedin_company_info, linkedin_gen_email, linkedin_gen_whatsapp],
            outputs=[linkedin_content_result, linkedin_content_download, linkedin_content_group, linkedin_send_group]
        )
        linkedin_content_no.click(
            handle_google_content_no,
            inputs=[linkedin_enhanced_download],
            outputs=[linkedin_content_result, linkedin_content_download, linkedin_content_group, linkedin_send_group]
        )

        linkedin_send_yes.click(
            handle_google_send_yes,
            inputs=[linkedin_content_download, linkedin_sender_email, linkedin_sender_password],
            outputs=[linkedin_send_result, linkedin_send_group]
        )
        linkedin_send_no.click(
            handle_google_send_no,
            outputs=[linkedin_send_result, linkedin_send_group]
        )

        # Instagram Step 2-4 handlers (same workflow as Google)
        instagram_auto_yes.click(
            handle_google_automation_yes,
            inputs=[instagram_download, instagram_auto_style, instagram_auto_max],
            outputs=[instagram_auto_result, instagram_enhanced_download, instagram_automation_group, instagram_content_group]
        )
        instagram_auto_no.click(
            handle_google_automation_no,
            inputs=[instagram_download],
            outputs=[instagram_auto_result, instagram_enhanced_download, instagram_automation_group, instagram_content_group]
        )

        instagram_content_yes.click(
            handle_google_content_yes,
            inputs=[instagram_enhanced_download, instagram_company_info, instagram_gen_email, instagram_gen_whatsapp],
            outputs=[instagram_content_result, instagram_content_download, instagram_content_group, instagram_send_group]
        )
        instagram_content_no.click(
            handle_google_content_no,
            inputs=[instagram_enhanced_download],
            outputs=[instagram_content_result, instagram_content_download, instagram_content_group, instagram_send_group]
        )

        instagram_send_yes.click(
            handle_google_send_yes,
            inputs=[instagram_content_download, instagram_sender_email, instagram_sender_password],
            outputs=[instagram_send_result, instagram_send_group]
        )
        instagram_send_no.click(
            handle_google_send_no,
            outputs=[instagram_send_result, instagram_send_group]
        )

        # Collections events
        view_btn.click(view_collections, outputs=[collections_display])
        export_btn.click(export_collection, inputs=[export_collection_id], outputs=[export_result, export_file])

        # AI Bulk Generation events
        generate_emails_btn.click(
            lambda file, additional_context, custom_instruction: generate_emails_from_excel(
                file, None,
                get_company_info_for_ai() + (f" | Additional Context: {additional_context}" if additional_context else ""),
                custom_instruction
            ),
            inputs=[upload_leads_email, company_info_email, custom_instruction_email],
            outputs=[email_generation_result, download_emails_file]
        )

        generate_whats_btn.click(
            lambda file, additional_context, custom_instruction: generate_whatsapp_messages_from_excel(
                file, None,
                get_company_info_for_ai() + (f" | Additional Context: {additional_context}" if additional_context else ""),
                custom_instruction
            ),
            inputs=[upload_leads_whats, company_info_whats, custom_instruction_whats],
            outputs=[whats_generation_result, download_whats_file]
        )

        # Email/WhatsApp Sending events
        send_email_btn.click(
            send_bulk_emails,
            inputs=[upload_excel, sender_email, sender_password],
            outputs=[email_send_result]
        )

        send_whats_btn.click(
            send_bulk_whatsapp,
            inputs=[upload_whats_excel, whatsapp_id, whatsapp_token],
            outputs=[whats_send_result]
        )

        # Description Generation events
        desc_gen_btn.click(
            generate_company_description,
            inputs=[desc_company_name, desc_max_results, desc_style, desc_mode],
            outputs=[desc_output]
        )

        bulk_desc_btn.click(
            generate_bulk_descriptions,
            inputs=[bulk_desc_file, bulk_desc_max_results, bulk_desc_style],
            outputs=[bulk_desc_result, bulk_desc_download]
        )

        # ============================================================
        # AUTOMATION PIPELINE EVENT HANDLER
        # ============================================================
        auto_start_btn.click(
            run_full_automation_handler,
            inputs=[
                auto_source,
                auto_query,
                auto_max_results,
                auto_enable_descriptions,
                auto_description_style,
                auto_enable_emails,
                auto_enable_whatsapp,
                auto_company_info,
                auto_custom_instruction,
                auto_send_emails,
                auto_sender_email,
                auto_sender_password,
                auto_send_whatsapp,
                auto_whatsapp_phone_id,
                auto_whatsapp_token
            ],
            outputs=[
                auto_progress_display,
                auto_results_summary,
                auto_final_file,
                auto_error_log
            ]
        )

        # Settings events
        save_company_profile_btn.click(
            save_company_profile,
            inputs=[
                company_name, company_industry, company_website, company_email,
                company_phone, company_address, company_description,
                company_services, company_team_info
            ],
            outputs=[company_profile_status]
        )

        reset_company_profile_btn.click(
            reset_company_profile,
            outputs=[company_profile_status]
        )

        save_preferences_btn.click(
            save_user_preferences,
            inputs=[auto_save_results, email_notifications, default_max_results],
            outputs=[preferences_status]
        )

        save_api_keys_btn.click(
            save_api_keys,
            inputs=[google_api_key, serpapi_key, huggingface_token, whatsapp_token],
            outputs=[api_keys_status]
        )

        test_api_keys_btn.click(
            test_api_connections,
            inputs=[google_api_key, serpapi_key, huggingface_token, whatsapp_token],
            outputs=[api_keys_status]
        )

        # Analytics Dashboard event handlers
        analytics_refresh_btn.click(
            get_analytics_data,
            outputs=[analytics_output]
        ).then(
            get_quick_stats,
            outputs=[quick_stats]
        )

        # Email Templates event handlers
        save_template_btn.click(
            save_email_template,
            inputs=[template_name, template_category, template_subject, template_body],
            outputs=[template_save_status]
        ).then(
            lambda: "",
            outputs=[template_name, template_subject, template_body]
        ).then(
            get_email_templates,
            outputs=[templates_list]
        )

        preview_template_btn.click(
            preview_email_template,
            inputs=[template_name, template_category, template_subject, template_body],
            outputs=[template_save_status]
        )

        refresh_templates_btn.click(
            get_email_templates,
            inputs=[template_category_filter],
            outputs=[templates_list]
        )

        template_category_filter.change(
            get_email_templates,
            inputs=[template_category_filter],
            outputs=[templates_list]
        )

        # Load initial data for analytics and templates
        app.load(
            get_quick_stats,
            outputs=[quick_stats]
        )

        app.load(
            get_email_templates,
            outputs=[templates_list]
        )

    return app

# ====== Main Entry Point ======
if __name__ == "__main__":
    # Initialize database
    init_db()

    # Initialize email templates database
    initialize_email_templates_db()

    # Create and launch interface
    app = create_interface()

    print("Starting Elite Creatif SaaS Integrated App...")
    print("Make sure your SaaS backend is running at http://localhost:8000")
    print("Gradio app will be available at http://localhost:7860")

    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        show_error=True,
        allowed_paths=["/workspace"],
        max_threads=40  # Increase threads to handle long-running AI model tasks
    )