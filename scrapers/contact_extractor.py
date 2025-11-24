import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import json
from typing import Set, List, Dict

class ContactExtractor:
    """Utility class for extracting contact information from websites"""

    def __init__(self):
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_patterns = [
            re.compile(r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),  # US format
            re.compile(r'(\+\d{1,4}[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}'),  # International
            re.compile(r'(\+\d{1,4}[-.\s]?)?\d{2,3}[-.\s]?\d{3,4}[-.\s]?\d{4,5}'),  # Alternative international
        ]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # Common email formats to try
        self.common_email_formats = [
            'info@{}', 'contact@{}', 'hello@{}', 'support@{}',
            'sales@{}', 'admin@{}', 'office@{}', 'mail@{}'
        ]

    def extract_emails_from_text(self, text):
        """Extract email addresses from text"""
        if not text:
            return []

        emails = self.email_pattern.findall(text.lower())
        # Filter out common non-business emails
        filtered_emails = []
        skip_domains = ['example.com', 'test.com', 'placeholder.com', 'domain.com']

        for email in emails:
            domain = email.split('@')[1] if '@' in email else ''
            if domain not in skip_domains and not any(skip in domain for skip in ['noreply', 'no-reply']):
                filtered_emails.append(email)

        return list(set(filtered_emails))  # Remove duplicates

    def extract_phones_from_text(self, text):
        """Extract phone numbers from text"""
        if not text:
            return []

        phones = []
        for pattern in self.phone_patterns:
            matches = pattern.findall(text)
            phones.extend(matches)

        # Clean and filter phone numbers
        cleaned_phones = []
        for phone in phones:
            # Remove common non-phone patterns
            if len(re.sub(r'\D', '', phone)) >= 10:  # At least 10 digits
                cleaned_phones.append(phone.strip())

        return list(set(cleaned_phones))  # Remove duplicates

    def extract_domain_from_url(self, url):
        """Extract domain from URL for email guessing"""
        try:
            domain = urlparse(url).netloc
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return None

    def guess_common_emails(self, domain):
        """Generate common email addresses for a domain"""
        if not domain:
            return []

        emails = []
        for format_template in self.common_email_formats:
            try:
                email = format_template.format(domain)
                emails.append(email)
            except:
                continue

        return emails

    def extract_social_media_emails(self, text, platform="general"):
        """Enhanced social media email extraction"""
        emails = self.extract_emails_from_text(text)

        # Platform-specific patterns
        if platform == "facebook":
            # Look for emails in Facebook page info
            fb_patterns = [
                r'Email[:\s]+([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
                r'Contact[:\s]+([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
                r'Reach us[:\s]+([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})'
            ]
            for pattern in fb_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                emails.extend(matches)

        return list(set(emails))

    def try_facebook_alternative_extraction(self, url):
        """Try alternative methods for Facebook pages"""
        contacts = {"emails": [], "phones": []}

        if 'facebook.com' not in url:
            return contacts

        try:
            # Try different approaches for Facebook
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
            }

            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Look for emails in meta tags
                for meta in soup.find_all('meta'):
                    content = meta.get('content', '')
                    emails = self.extract_social_media_emails(content, 'facebook')
                    contacts['emails'].extend(emails)

                # Look for structured data
                scripts = soup.find_all('script', type='application/ld+json')
                for script in scripts:
                    try:
                        data = json.loads(script.string)
                        if isinstance(data, dict):
                            email = data.get('email')
                            if email:
                                contacts['emails'].append(email)
                    except:
                        continue

        except Exception as e:
            print(f"Facebook alternative extraction failed: {e}")

        return contacts

    def scrape_website_contacts(self, url, timeout=10):
        """Enhanced website contact scraping with multiple strategies"""
        contacts = {
            'emails': [],
            'phones': [],
            'contact_page_url': None
        }

        if not url or not url.startswith(('http://', 'https://')):
            return contacts

        # Strategy 1: Try Facebook alternative extraction if it's a Facebook page
        if 'facebook.com' in url:
            fb_contacts = self.try_facebook_alternative_extraction(url)
            contacts['emails'].extend(fb_contacts['emails'])
            contacts['phones'].extend(fb_contacts['phones'])

        # Strategy 2: Regular website scraping
        try:
            response = requests.get(url, headers=self.headers, timeout=timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract contacts from main page
            page_text = soup.get_text()
            contacts['emails'].extend(self.extract_emails_from_text(page_text))
            contacts['phones'].extend(self.extract_phones_from_text(page_text))

            # Look for emails in meta tags
            for meta in soup.find_all('meta'):
                content = meta.get('content', '')
                if content:
                    contacts['emails'].extend(self.extract_emails_from_text(content))

            # Look for structured data (JSON-LD)
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    self._extract_from_structured_data(data, contacts)
                except:
                    continue

            # Look for contact page
            contact_urls = self.find_contact_page_urls(soup, url)

            # Try to scrape contact pages
            for contact_url in contact_urls[:2]:  # Limit to 2 contact pages
                try:
                    time.sleep(1)  # Be respectful
                    contact_response = requests.get(contact_url, headers=self.headers, timeout=timeout)
                    contact_response.raise_for_status()
                    contact_soup = BeautifulSoup(contact_response.text, 'html.parser')

                    contact_text = contact_soup.get_text()
                    contacts['emails'].extend(self.extract_emails_from_text(contact_text))
                    contacts['phones'].extend(self.extract_phones_from_text(contact_text))

                    if not contacts['contact_page_url']:
                        contacts['contact_page_url'] = contact_url

                except:
                    continue

        except Exception as e:
            print(f"Error scraping {url}: {e}")

        # Strategy 3: No email guessing - only return found emails

        # Remove duplicates
        contacts['emails'] = list(set(contacts['emails']))
        contacts['phones'] = list(set(contacts['phones']))

        return contacts

    def _extract_from_structured_data(self, data, contacts):
        """Extract contacts from structured data (JSON-LD)"""
        if isinstance(data, dict):
            # Look for email
            email = data.get('email')
            if email:
                contacts['emails'].append(email)

            # Look for phone
            phone = data.get('telephone') or data.get('phone')
            if phone:
                contacts['phones'].append(phone)

            # Look for contact info in nested objects
            contact_point = data.get('contactPoint', {})
            if isinstance(contact_point, dict):
                email = contact_point.get('email')
                phone = contact_point.get('telephone')
                if email:
                    contacts['emails'].append(email)
                if phone:
                    contacts['phones'].append(phone)

        elif isinstance(data, list):
            for item in data:
                self._extract_from_structured_data(item, contacts)

    def find_contact_page_urls(self, soup, base_url):
        """Find potential contact page URLs"""
        contact_urls = []
        contact_keywords = ['contact', 'about', 'team', 'reach', 'get-in-touch']

        # Find links that might lead to contact information
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            link_text = link.get_text().lower()

            # Check if link text or href contains contact keywords
            if any(keyword in href or keyword in link_text for keyword in contact_keywords):
                full_url = urljoin(base_url, link['href'])
                if full_url not in contact_urls and self.is_same_domain(base_url, full_url):
                    contact_urls.append(full_url)

        return contact_urls

    def is_same_domain(self, url1, url2):
        """Check if two URLs are from the same domain"""
        try:
            domain1 = urlparse(url1).netloc
            domain2 = urlparse(url2).netloc
            return domain1 == domain2
        except:
            return False

    def extract_social_media_contacts(self, text, platform="general"):
        """Extract contact info from social media platform text"""
        emails = self.extract_emails_from_text(text)
        phones = self.extract_phones_from_text(text)

        # Platform-specific extraction
        if platform == "linkedin":
            # LinkedIn often has emails in company descriptions
            pass
        elif platform == "instagram":
            # Instagram bios might have contact info
            pass

        return {
            'emails': emails,
            'phones': phones
        }

# Global instance for easy use
contact_extractor = ContactExtractor()