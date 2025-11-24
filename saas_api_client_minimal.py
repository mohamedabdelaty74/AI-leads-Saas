# Elite Creatif SaaS API Client - Minimal Version
import os
import requests
import json
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

class EliteCreatifSaaSClient:
    def __init__(self, base_url: str = None):
        # Auto-detect backend URL - use env variable or default
        if base_url is None:
            base_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        self.base_url = base_url
        self.token = None
        self.organization_id = None
        self.user_id = None

    def login(self, email: str, password: str) -> bool:
        """Login to SaaS backend and get access token"""
        try:
            # Use JSON data for UserLogin model
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"email": email, "password": password},
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                user = data.get("user", {})
                self.user_id = user.get("id")
                self.organization_id = user.get("tenant_id")  # New backend has tenant_id
                print(f"[SUCCESS] Logged in as {user.get('first_name')} {user.get('last_name')}")
                return True
            else:
                print(f"Login failed: {response.text}")
                return False

        except Exception as e:
            print(f"Login error: {e}")
            return False

    def register_organization(self, org_name: str, admin_email: str, admin_password: str) -> bool:
        """Register new organization and admin user"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/auth/register",
                json={
                    "company_name": org_name,
                    "company_email": admin_email,
                    "email": admin_email,
                    "password": admin_password,
                    "first_name": org_name.split()[0] if org_name.split() else "Admin",
                    "last_name": "Admin"
                },
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 201:  # New backend returns 201 for registration
                data = response.json()
                # Extract token and user data
                self.token = data.get("access_token")
                user = data.get("user", {})
                self.user_id = user.get("id")
                self.organization_id = user.get("tenant_id")  # New backend has tenant_id
                print(f"[SUCCESS] Registered as {user.get('first_name')} {user.get('last_name')}")
                return True
            else:
                print(f"Registration failed: {response.text}")
                return False

        except Exception as e:
            print(f"Registration error: {e}")
            return False

    def create_lead_collection(self, name: str, source_type: str, query_params: Dict) -> Optional[str]:
        """Create a new campaign (replaces lead collection)"""
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            } if self.token else {"Content-Type": "application/json"}

            # Map to new campaign structure
            campaign_data = {
                "name": name,
                "description": f"Auto-generated campaign from {source_type}",
                "search_query": query_params.get("query", ""),
                "lead_source": source_type,
                "max_leads": query_params.get("max_results", 10),
                "description_style": "professional",
                "enable_ai_personalization": True
            }

            response = requests.post(
                f"{self.base_url}/api/v1/campaigns",
                json=campaign_data,
                headers=headers
            )

            if response.status_code == 201:
                return response.json().get("id")
            else:
                print(f"Failed to create campaign: {response.text}")
                return None

        except Exception as e:
            print(f"Error creating campaign: {e}")
            return None

    def add_leads_to_collection(self, collection_id: str, leads_data: List[Dict]) -> bool:
        """Add multiple leads to a campaign"""
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            } if self.token else {"Content-Type": "application/json"}

            # Prepare leads data - convert DataFrame columns to API schema
            cleaned_leads = []
            for lead in leads_data:
                cleaned_lead = {
                    "title": lead.get("Title") or lead.get("title") or "",
                    "address": lead.get("Address") or lead.get("address") or "",
                    "phone": lead.get("Phone") or lead.get("phone") or "",
                    "website": lead.get("Website") or lead.get("website") or "",
                    "email": lead.get("Email") or lead.get("email") or "",
                    "contact_source": lead.get("Contact_Source") or lead.get("contact_source") or "",
                    "lead_score": 50,
                    "scraped_data": lead  # Store full original data
                }
                cleaned_leads.append(cleaned_lead)

            # Upload to backend
            response = requests.post(
                f"{self.base_url}/api/v1/campaigns/{collection_id}/leads/bulk",
                json=cleaned_leads,
                headers=headers
            )

            if response.status_code == 201:
                result = response.json()
                print(f"[SUCCESS] Uploaded {result.get('leads_added', len(cleaned_leads))} leads to campaign {collection_id}")
                return True
            else:
                print(f"[WARNING] Failed to upload leads: {response.text}")
                print(f"[INFO] Leads saved locally in Excel file")
                return False

        except Exception as e:
            print(f"[ERROR] Error uploading leads: {e}")
            print(f"[INFO] Leads saved locally in Excel file")
            return False

    def get_collections(self) -> List[Dict]:
        """Get all campaigns for the organization"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
            response = requests.get(f"{self.base_url}/api/v1/campaigns", headers=headers)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get campaigns: {response.text}")
                return []

        except Exception as e:
            print(f"Error getting campaigns: {e}")
            return []

    def get_collection_leads(self, collection_id: str) -> List[Dict]:
        """Get all leads from a campaign"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
            response = requests.get(f"{self.base_url}/api/v1/campaigns/{collection_id}/leads", headers=headers)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get leads: {response.text}")
                return []

        except Exception as e:
            print(f"Error getting leads: {e}")
            return []

    def scrape_and_save_google_leads(self, query: str, max_results: int = 10) -> Optional[str]:
        """Scrape Google Maps leads and save to SaaS backend"""
        # Import your enhanced scraper
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), "scrapers"))
        from google_scrapers_fixed import collect_google_leads

        try:
            # Create collection
            collection_id = self.create_lead_collection(
                name=f"Google Maps: {query}",
                source_type="google_maps",
                query_params={"query": query, "max_results": max_results}
            )

            if not collection_id:
                return None

            # Scrape leads (this creates an Excel file)
            excel_file = collect_google_leads(query, max_results)

            # Check if file was created
            if not excel_file or not os.path.exists(excel_file):
                print(f"[ERROR] Scraping failed - no Excel file created")
                return collection_id  # Return campaign ID even if scraping failed

            # Read Excel and convert to list of dicts
            import pandas as pd
            df = pd.read_excel(excel_file)

            # Check if we got any real data (not just sample error data)
            if len(df) == 0:
                print(f"[WARNING] No leads found in Excel file")
                return collection_id

            # Fill NaN values with empty strings to avoid JSON errors
            df = df.fillna("")
            leads_data = df.to_dict('records')

            # Save to SaaS backend
            self.add_leads_to_collection(collection_id, leads_data)

            # Return campaign ID (Excel file kept for workflow)
            return collection_id

        except Exception as e:
            print(f"[ERROR] Error in scrape_and_save_google_leads: {e}")
            import traceback
            traceback.print_exc()
            return collection_id if collection_id else None

    def scrape_and_save_linkedin_leads(self, query: str, max_results: int = 5) -> Optional[str]:
        """Scrape LinkedIn leads and save to SaaS backend"""
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), "scrapers"))
        from linkedin_scraper import collect_linkedin_leads

        try:
            collection_id = self.create_lead_collection(
                name=f"LinkedIn: {query}",
                source_type="linkedin",
                query_params={"query": query, "max_results": max_results}
            )

            if not collection_id:
                return None

            excel_file = collect_linkedin_leads(query, max_results)

            import pandas as pd
            df = pd.read_excel(excel_file)
            df = df.fillna("")  # Fix NaN values
            leads_data = df.to_dict('records')

            # Save to SaaS backend (currently just logs, doesn't upload)
            self.add_leads_to_collection(collection_id, leads_data)

            # Return campaign ID (Excel file kept for workflow)
            return collection_id

        except Exception as e:
            print(f"Error in scrape_and_save_linkedin_leads: {e}")
            return None

    def scrape_and_save_instagram_leads(self, query: str, max_results: int = 5) -> Optional[str]:
        """Scrape Instagram leads and save to SaaS backend"""
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), "scrapers"))
        from instagram_scraper import collect_instagram_leads

        try:
            collection_id = self.create_lead_collection(
                name=f"Instagram: {query}",
                source_type="instagram",
                query_params={"query": query, "max_results": max_results}
            )

            if not collection_id:
                return None

            excel_file = collect_instagram_leads(query, max_results)

            import pandas as pd
            df = pd.read_excel(excel_file)
            df = df.fillna("")  # Fix NaN values
            leads_data = df.to_dict('records')

            # Save to SaaS backend (currently just logs, doesn't upload)
            self.add_leads_to_collection(collection_id, leads_data)

            # Return campaign ID (Excel file kept for workflow)
            return collection_id

        except Exception as e:
            print(f"Error in scrape_and_save_instagram_leads: {e}")
            return None

# Global client instance
saas_client = EliteCreatifSaaSClient()

# Helper functions for easy use
def login_to_saas(email: str, password: str) -> bool:
    """Simple login function"""
    return saas_client.login(email, password)

def register_saas_org(org_name: str, admin_email: str, admin_password: str) -> bool:
    """Simple organization registration"""
    return saas_client.register_organization(org_name, admin_email, admin_password)