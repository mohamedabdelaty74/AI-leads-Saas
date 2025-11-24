import os
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from serpapi import GoogleSearch
from dotenv import load_dotenv
from tenacity import retry, wait_exponential, stop_after_attempt
from scrapers.contact_extractor import contact_extractor

load_dotenv()

# ✅ سكراب لنتائج شركات من لينكدإن عبر بحث Google
@retry(wait=wait_exponential(min=1, max=30), stop=stop_after_attempt(5))
def get_linkedin_companies(query, max_results=5, pause=1.5):
    results = []
    seen_urls = set()
    gquery = f"site:linkedin.com/company {query}"

    # Use SERPAPI instead of googlesearch
    search_params = {
        "engine": "google",
        "q": gquery,
        "api_key": os.getenv("SERPAPI_KEY"),
        "num": min(50, max_results * 3)  # Get more results to filter
    }
    
    try:
        search_results = GoogleSearch(search_params)
        data = search_results.get_dict()
        organic_results = data.get("organic_results", [])
        
        for result in organic_results:
            url = result.get("link", "")
            if "linkedin.com/company/" not in url or url in seen_urls:
                continue

            try:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                resp = requests.get(url, headers=headers, timeout=10)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                title = soup.find("title").get_text(strip=True) if soup.find("title") else result.get("title", url)

                # Clean up title by removing "| LinkedIn" suffix
                if title.endswith("| LinkedIn"):
                    title = title[:-10].strip()  # Remove "| LinkedIn" and trailing spaces
                elif " | LinkedIn" in title:
                    title = title.split(" | LinkedIn")[0].strip()  # Handle variations with different spacing

                meta = (
                    soup.find("meta", property="og:description") or
                    soup.find("meta", attrs={"name": "description"})
                )
                desc = meta["content"].strip() if meta and meta.get("content") else result.get("snippet", "")

                # Extract contact information from LinkedIn page and description
                page_text = soup.get_text() + " " + desc
                extracted_contacts = contact_extractor.extract_social_media_contacts(page_text, "linkedin")

                # Try to find company website from LinkedIn page
                website = ""
                website_links = soup.find_all('a', href=True)
                for link in website_links:
                    href = link['href']
                    if any(domain not in href for domain in ['linkedin.com', 'facebook.com', 'twitter.com', 'instagram.com']):
                        if href.startswith('http') and 'linkedin.com' not in href:
                            website = href
                            break

                results.append({
                    "Title": title,
                    "LinkedIn": url,
                    "Website": website,
                    "Email": "; ".join(extracted_contacts.get("emails", [])) if extracted_contacts.get("emails") else "Not Found",
                    "Phone": "; ".join(extracted_contacts.get("phones", [])) if extracted_contacts.get("phones") else "",
                    "Description": desc
                })
                seen_urls.add(url)

            except Exception:
                # Use SERPAPI data as fallback
                fallback_title = result.get("title", "")

                # Clean up fallback title by removing "| LinkedIn" suffix
                if fallback_title.endswith("| LinkedIn"):
                    fallback_title = fallback_title[:-10].strip()
                elif " | LinkedIn" in fallback_title:
                    fallback_title = fallback_title.split(" | LinkedIn")[0].strip()

                # Extract contacts from fallback snippet
                snippet = result.get("snippet", "")
                fallback_contacts = contact_extractor.extract_social_media_contacts(snippet, "linkedin")

                results.append({
                    "Title": fallback_title,
                    "LinkedIn": url,
                    "Website": "",
                    "Email": "; ".join(fallback_contacts.get("emails", [])) if fallback_contacts.get("emails") else "Not Found",
                    "Phone": "; ".join(fallback_contacts.get("phones", [])) if fallback_contacts.get("phones") else "",
                    "Description": snippet
                })
                seen_urls.add(url)

            time.sleep(pause)
            if len(results) >= max_results:
                break
                
    except Exception as e:
        print(f"SERPAPI search failed: {e}")

    return pd.DataFrame(results)

# ✅ الدالة النهائية لحفظ النتائج
def collect_linkedin_leads(query, max_results=5, output_path="linkedin_leads.xlsx", return_preview=False):
    df = get_linkedin_companies(query, max_results=max_results)

    # Generate filename with timestamp if not provided
    if output_path == "linkedin_leads.xlsx":
        import time
        output_path = f"linkedin_leads_{int(time.time())}.xlsx"

    df.to_excel(output_path, index=False)

    if return_preview:
        # Convert DataFrame to list of dictionaries for preview
        data = df.to_dict('records')
        return output_path, data

    return output_path
