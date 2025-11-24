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

@retry(wait=wait_exponential(min=1, max=30), stop=stop_after_attempt(5))
def get_instagram_profiles(query, max_results=5, pause=1.5):
    results = []
    seen_urls = set()
    gquery = f"site:instagram.com {query}"

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
            if 'instagram.com/' not in url or any(x in url for x in ['/p/', '/tv/', '/reel/']):
                continue
            if url in seen_urls:
                continue
                
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                resp = requests.get(url, headers=headers, timeout=10)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, 'html.parser')

                title_tag = soup.find('title')
                profile_name = title_tag.get_text(strip=True).split('(')[0].strip() if title_tag else result.get("title", url)

                meta_desc = soup.find('meta', attrs={'name': 'description'})
                bio = ''
                description = ''
                if meta_desc and meta_desc.get('content'):
                    content = meta_desc['content']
                    parts = content.split('Instagram')
                    bio = parts[0].strip() if parts else ''
                    if len(parts) > 1:
                        description = parts[1].split('•')[0].strip()

                # Extract contact information from Instagram bio and page content
                full_text = f"{bio} {description} {soup.get_text()}"
                extracted_contacts = contact_extractor.extract_social_media_contacts(full_text, "instagram")

                # Look for website/link in bio (Instagram often has link in bio)
                external_website = ""
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.startswith('http') and 'instagram.com' not in href:
                        external_website = href
                        break

                results.append({
                    'Profile Name': profile_name,
                    'URL': url,
                    'Website': external_website,
                    'Email': "; ".join(extracted_contacts.get("emails", [])) if extracted_contacts.get("emails") else "Not Found",
                    'Phone': "; ".join(extracted_contacts.get("phones", [])) if extracted_contacts.get("phones") else "",
                    'Bio': bio,
                    'Description': description
                })
                seen_urls.add(url)
                
            except Exception:
                # Use SERPAPI data as fallback
                snippet = result.get("snippet", "")
                fallback_contacts = contact_extractor.extract_social_media_contacts(snippet, "instagram")

                results.append({
                    'Profile Name': result.get("title", ""),
                    'URL': url,
                    'Website': "",
                    'Email': "; ".join(fallback_contacts.get("emails", [])) if fallback_contacts.get("emails") else "Not Found",
                    'Phone': "; ".join(fallback_contacts.get("phones", [])) if fallback_contacts.get("phones") else "",
                    'Bio': snippet,
                    'Description': ""
                })
                seen_urls.add(url)

            time.sleep(pause)
            if len(results) >= max_results:
                break
                
    except Exception as e:
        print(f"SERPAPI search failed: {e}")

    return pd.DataFrame(results)

def collect_instagram_leads(query, max_results=5, output_path="instagram_leads.xlsx", return_preview=False):
    df = get_instagram_profiles(query, max_results=max_results)

    # Generate filename with timestamp if not provided
    if output_path == "instagram_leads.xlsx":
        import time
        output_path = f"instagram_leads_{int(time.time())}.xlsx"

    df.to_excel(output_path, index=False)

    if return_preview:
        # Convert DataFrame to list of dictionaries for preview
        data = df.to_dict('records')
        return output_path, data

    return output_path
