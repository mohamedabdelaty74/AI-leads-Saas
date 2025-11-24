import os
import re
import time
import requests
import pandas as pd
import googlemaps
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from tenacity import retry, wait_exponential, stop_after_attempt

# Import contact extractor
try:
    from .contact_extractor import contact_extractor
except ImportError:
    # If relative import fails, try absolute
    import sys
    sys.path.append(os.path.dirname(__file__))
    from contact_extractor import contact_extractor

# Load API key from env
load_dotenv()

def init_gmaps():
    """Initialize Google Maps client with error handling"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")

    try:
        gmaps = googlemaps.Client(key=api_key)
        # Test the connection
        gmaps.geocode("New York")
        return gmaps
    except Exception as e:
        print(f"Google Maps API Error: {e}")
        return None

# Initialize with error handling
try:
    gmaps = init_gmaps()
except Exception as e:
    print(f"Failed to initialize Google Maps: {e}")
    gmaps = None

@retry(wait=wait_exponential(min=1, max=20), stop=stop_after_attempt(3))
def get_details(place_id):
    """Get place details with error handling"""
    if not gmaps:
        return {
            "name": "API Error",
            "address": "API not available",
            "phone": "",
            "website": ""
        }

    try:
        fields = ["name", "formatted_address", "formatted_phone_number", "website"]
        result = gmaps.place(place_id=place_id, fields=fields)

        if 'result' not in result:
            print(f"No result for place_id: {place_id}")
            return {
                "name": "Unknown",
                "address": "Unknown",
                "phone": "",
                "website": ""
            }

        detail = result.get("result", {})
        return {
            "name": detail.get("name", "Unknown"),
            "address": detail.get("formatted_address", "Unknown"),
            "phone": detail.get("formatted_phone_number", ""),
            "website": detail.get("website", "")
        }
    except Exception as e:
        print(f"Error getting details for {place_id}: {e}")
        return {
            "name": "Error",
            "address": "Error retrieving details",
            "phone": "",
            "website": ""
        }

def enhanced_contact_extraction(url):
    """Enhanced contact extraction using our contact_extractor utility"""
    if not url or url == "":
        return {"emails": [], "phones": []}

    try:
        # Use our enhanced contact extractor
        contacts = contact_extractor.scrape_website_contacts(url, timeout=10)
        return {
            "emails": contacts.get("emails", []),
            "phones": contacts.get("phones", [])
        }
    except Exception as e:
        print(f"Error extracting contacts from {url}: {e}")
        return {"emails": [], "phones": []}

def collect_google_leads(query, max_results, return_preview=False):
    """Collect Google Maps leads with comprehensive error handling"""
    print(f"Starting Google Maps search for: {query}")

    if not gmaps:
        print("❌ Google Maps API not available")
        # Return sample data so the system doesn't crash
        sample_data = [{
            "Title": "Sample Business",
            "Address": "123 Main St, Sample City",
            "Phone": "+1-555-0123",
            "Website": "https://example.com",
            "Email": "contact@example.com",
            "Contact_Source": "API Error",
            "Email_Count": 1,
            "Phone_Count": 1
        }]
        df = pd.DataFrame(sample_data)
        output_file = f"google_maps_leads_{int(time.time())}.xlsx"
        df.to_excel(output_file, index=False)
        print(f"❌ API Error - Created sample file: {output_file}")

        if return_preview:
            return output_file, sample_data
        return output_file

    try:
        max_results = min(int(max_results), 50)  # Limit to prevent API overuse
        print(f"Searching for up to {max_results} results...")

        # Initial search
        res = gmaps.places(query=query)
        if 'results' not in res:
            print("❌ No results found in API response")
            raise Exception("No results in API response")

        results = res.get("results", [])
        print(f"Found {len(results)} initial results")

        # Get additional pages if needed
        while "next_page_token" in res and len(results) < max_results:
            print(f"Getting next page... Current count: {len(results)}")
            time.sleep(2)  # Required delay for next_page_token
            try:
                res = gmaps.places(query=query, page_token=res["next_page_token"])
                new_results = res.get("results", [])
                results.extend(new_results)
                print(f"Added {len(new_results)} more results")
            except Exception as e:
                print(f"Error getting next page: {e}")
                break

        # Limit results
        results = results[:max_results]
        print(f"Processing {len(results)} final results...")

        def process_place(place):
            """Process a single place with error handling"""
            try:
                place_id = place.get("place_id")
                if not place_id:
                    return {
                        "Title": place.get("name", "Unknown"),
                        "Address": "No address available",
                        "Phone": "",
                        "Website": "",
                        "Email": "",
                    }

                info = get_details(place_id)

                # Enhanced contact extraction if website available
                extracted_contacts = {"emails": [], "phones": []}
                if info.get("website"):
                    extracted_contacts = enhanced_contact_extraction(info["website"])
                    print(f"  → Found {len(extracted_contacts.get('emails', []))} emails, {len(extracted_contacts.get('phones', []))} phones from website")

                # Get extracted emails (no guessing)
                all_emails = extracted_contacts.get("emails", [])

                # Combine all phone numbers (Google Maps + website extraction)
                all_phones = []
                if info.get("phone"):
                    all_phones.append(info["phone"])
                all_phones.extend(extracted_contacts.get("phones", []))

                return {
                    "Title": info["name"],
                    "Address": info["address"],
                    "Phone": "; ".join(list(set(all_phones))) if all_phones else "",
                    "Website": info["website"],
                    "Email": "; ".join(all_emails) if all_emails else "Not Found",
                    "Contact_Source": "Google Maps + Website" if info.get("website") else "Google Maps Only",
                    "Email_Count": len(all_emails),
                    "Phone_Count": len(all_phones)
                }
            except Exception as e:
                print(f"Error processing place: {e}")
                return {
                    "Title": place.get("name", "Error"),
                    "Address": "Error processing",
                    "Phone": "",
                    "Website": "",
                    "Email": "",
                }

        # Process places with threading
        workers = min(5, len(results))  # Limit concurrent requests
        print(f"Processing with {workers} workers...")

        with ThreadPoolExecutor(max_workers=workers) as executor:
            data = list(executor.map(process_place, results))

        # Filter out completely empty results
        data = [d for d in data if d["Title"] and d["Title"] != "Error"]

        if not data:
            print("❌ No valid data collected")
            # Return sample data
            data = [{
                "Title": "No results found",
                "Address": "Try a different search query",
                "Phone": "",
                "Website": "",
                "Email": "",
            }]

        # Create DataFrame and save
        df = pd.DataFrame(data)
        output_file = f"google_maps_leads_{int(time.time())}.xlsx"
        df.to_excel(output_file, index=False)

        print(f"✅ Successfully collected {len(data)} leads and saved to {output_file}")

        if return_preview:
            return output_file, data
        return output_file

    except Exception as e:
        print(f"❌ Error in collect_google_leads: {e}")
        # Return sample data so system doesn't crash
        sample_data = [{
            "Title": f"Search Error: {query}",
            "Address": f"Error: {str(e)}",
            "Phone": "",
            "Website": "",
            "Email": "",
            "Contact_Source": "Error",
            "Email_Count": 0,
            "Phone_Count": 0
        }]
        df = pd.DataFrame(sample_data)
        output_file = f"google_maps_error_{int(time.time())}.xlsx"
        df.to_excel(output_file, index=False)
        print(f"❌ Created error file: {output_file}")

        if return_preview:
            return output_file, sample_data
        return output_file

# Test function
if __name__ == "__main__":
    try:
        result = collect_google_leads("coffee shops in New York", 5)
        print(f"Test result: {result}")
    except Exception as e:
        print(f"Test failed: {e}")