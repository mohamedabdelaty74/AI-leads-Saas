"""
Website Scraper Service
Visits lead websites and extracts contact information (emails, phones, social links)
"""

import os
import re
import logging
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


class WebsiteScraperError(Exception):
    """Custom exception for website scraper errors"""
    pass


class WebsiteContactExtractor:
    """Extract contact information from website pages"""

    def __init__(self):
        # Email patterns
        self.email_patterns = [
            re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            re.compile(r'mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})', re.IGNORECASE),
        ]

        # Phone patterns - international formats
        self.phone_patterns = [
            re.compile(r'tel:([+\d\s\-().]+)', re.IGNORECASE),
            re.compile(r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),
            re.compile(r'(\+\d{1,4}[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}'),
            re.compile(r'\+971[\s-]?\d{1,2}[\s-]?\d{3}[\s-]?\d{4}'),  # UAE
            re.compile(r'\+20[\s-]?\d{2,3}[\s-]?\d{3}[\s-]?\d{4}'),   # Egypt
            re.compile(r'\+966[\s-]?\d{1,2}[\s-]?\d{3}[\s-]?\d{4}'),  # Saudi
        ]

        # WhatsApp patterns
        self.whatsapp_patterns = [
            re.compile(r'wa\.me/(\d+)', re.IGNORECASE),
            re.compile(r'whatsapp\.com/send\?phone=(\d+)', re.IGNORECASE),
            re.compile(r'api\.whatsapp\.com/send\?phone=(\d+)', re.IGNORECASE),
        ]

        # Social media patterns
        self.social_patterns = {
            'linkedin': re.compile(r'linkedin\.com/(?:in|company)/([^/\s"\'<>]+)', re.IGNORECASE),
            'twitter': re.compile(r'(?:twitter|x)\.com/([^/\s"\'<>]+)', re.IGNORECASE),
            'facebook': re.compile(r'facebook\.com/([^/\s"\'<>]+)', re.IGNORECASE),
            'instagram': re.compile(r'instagram\.com/([^/\s"\'<>]+)', re.IGNORECASE),
        }

        # Common contact page paths to check
        self.contact_paths = [
            '/contact', '/contact-us', '/contactus', '/contact.html',
            '/about', '/about-us', '/aboutus', '/about.html',
            '/get-in-touch', '/reach-us', '/support',
        ]

    def extract_emails(self, text: str, html: str = '') -> List[str]:
        """Extract email addresses from text and HTML"""
        emails = set()

        # Search in plain text
        for pattern in self.email_patterns:
            matches = pattern.findall(text.lower())
            for match in matches:
                email = match if isinstance(match, str) else match[0]
                if self._is_valid_email(email):
                    emails.add(email)

        # Search in HTML (for mailto links)
        if html:
            for pattern in self.email_patterns:
                matches = pattern.findall(html.lower())
                for match in matches:
                    email = match if isinstance(match, str) else match[0]
                    if self._is_valid_email(email):
                        emails.add(email)

        return list(emails)

    def _is_valid_email(self, email: str) -> bool:
        """Validate email address"""
        skip_domains = [
            'example.com', 'test.com', 'placeholder.com', 'domain.com',
            'yourcompany.com', 'company.com', 'email.com', 'wixpress.com',
            'sentry.io', 'sentry-next.wixpress.com'
        ]
        skip_keywords = ['noreply', 'no-reply', 'donotreply', 'mailer-daemon',
                        'webmaster', 'hostmaster', 'postmaster']

        if '@' not in email or len(email) < 5:
            return False

        domain = email.split('@')[1]
        if domain in skip_domains:
            return False

        for keyword in skip_keywords:
            if keyword in email.lower():
                return False

        # Skip image extensions in email (common false positives)
        if any(ext in email for ext in ['.png', '.jpg', '.gif', '.svg', '.css', '.js']):
            return False

        return True

    def extract_phones(self, text: str, html: str = '') -> List[str]:
        """Extract phone numbers from text and HTML"""
        phones = set()

        combined = f"{text} {html}"

        for pattern in self.phone_patterns:
            matches = pattern.findall(combined)
            for match in matches:
                phone = match if isinstance(match, str) else ''.join(match)
                phone = phone.strip()
                # Validate: at least 9 digits
                digits = re.sub(r'\D', '', phone)
                if len(digits) >= 9 and len(digits) <= 15:
                    phones.add(phone)

        return list(phones)

    def extract_whatsapp(self, html: str) -> Optional[str]:
        """Extract WhatsApp number from HTML"""
        for pattern in self.whatsapp_patterns:
            match = pattern.search(html)
            if match:
                number = match.group(1)
                if len(number) >= 10:
                    return f"+{number}"
        return None

    def extract_social_links(self, html: str) -> Dict[str, str]:
        """Extract social media links from HTML"""
        social = {}
        for platform, pattern in self.social_patterns.items():
            match = pattern.search(html)
            if match:
                username = match.group(1)
                # Skip common non-profile paths
                if username.lower() not in ['share', 'sharer', 'intent', 'home', 'login']:
                    social[platform] = username
        return social


extractor = WebsiteContactExtractor()


def scrape_website_contacts(url: str, follow_contact_page: bool = True) -> Dict:
    """
    Scrape a website for contact information

    Args:
        url: The website URL to scrape
        follow_contact_page: Whether to also check common contact page URLs

    Returns:
        Dictionary with extracted contact information
    """
    if not url:
        return {'error': 'No URL provided'}

    # Ensure URL has protocol
    if not url.startswith('http'):
        url = f'https://{url}'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }

    all_emails = set()
    all_phones = set()
    whatsapp = None
    social_links = {}
    pages_checked = []

    try:
        # First, scrape the main page
        result = _scrape_single_page(url, headers)
        if result:
            all_emails.update(result.get('emails', []))
            all_phones.update(result.get('phones', []))
            if result.get('whatsapp'):
                whatsapp = result['whatsapp']
            social_links.update(result.get('social', {}))
            pages_checked.append(url)

        # Optionally check contact pages
        if follow_contact_page:
            base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"

            for path in extractor.contact_paths:
                if len(all_emails) >= 3 and len(all_phones) >= 2:
                    break  # We have enough contact info

                contact_url = urljoin(base_url, path)
                if contact_url in pages_checked:
                    continue

                result = _scrape_single_page(contact_url, headers)
                if result and not result.get('error'):
                    all_emails.update(result.get('emails', []))
                    all_phones.update(result.get('phones', []))
                    if not whatsapp and result.get('whatsapp'):
                        whatsapp = result['whatsapp']
                    social_links.update(result.get('social', {}))
                    pages_checked.append(contact_url)

        return {
            'success': True,
            'url': url,
            'emails': list(all_emails)[:5],  # Limit to 5 emails
            'phones': list(all_phones)[:3],   # Limit to 3 phones
            'whatsapp': whatsapp,
            'social': social_links,
            'pages_checked': len(pages_checked),
        }

    except requests.exceptions.Timeout:
        logger.warning(f"Timeout scraping {url}")
        return {'success': False, 'error': 'Request timeout', 'url': url}
    except requests.exceptions.ConnectionError:
        logger.warning(f"Connection error for {url}")
        return {'success': False, 'error': 'Connection failed', 'url': url}
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return {'success': False, 'error': str(e), 'url': url}


def _scrape_single_page(url: str, headers: dict) -> Optional[Dict]:
    """Scrape a single page for contact information"""
    try:
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)

        if response.status_code != 200:
            return None

        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

        # Remove script and style elements
        for element in soup(['script', 'style', 'noscript']):
            element.decompose()

        text = soup.get_text(separator=' ', strip=True)

        emails = extractor.extract_emails(text, html)
        phones = extractor.extract_phones(text, html)
        whatsapp = extractor.extract_whatsapp(html)
        social = extractor.extract_social_links(html)

        return {
            'emails': emails,
            'phones': phones,
            'whatsapp': whatsapp,
            'social': social,
        }

    except Exception as e:
        logger.debug(f"Failed to scrape {url}: {e}")
        return None


def enrich_lead_from_website(lead_data: Dict) -> Dict:
    """
    Enrich a lead's contact information by scraping their website

    Args:
        lead_data: Dictionary containing lead info with 'website' key

    Returns:
        Updated lead data with enriched contact information
    """
    website = lead_data.get('website') or lead_data.get('scraped_data', {}).get('external_website')

    if not website:
        return {
            'success': False,
            'error': 'No website URL available for this lead',
            'lead': lead_data
        }

    # Skip social media URLs
    social_domains = ['instagram.com', 'facebook.com', 'twitter.com', 'linkedin.com', 'tiktok.com']
    if any(domain in website.lower() for domain in social_domains):
        return {
            'success': False,
            'error': 'Cannot scrape social media profiles directly',
            'lead': lead_data
        }

    # Scrape the website
    result = scrape_website_contacts(website)

    if not result.get('success'):
        return {
            'success': False,
            'error': result.get('error', 'Failed to scrape website'),
            'lead': lead_data
        }

    # Update lead data with found information
    updated = False

    # Add emails if lead doesn't have one
    if not lead_data.get('email') and result.get('emails'):
        lead_data['email'] = '; '.join(result['emails'])
        updated = True
    elif result.get('emails'):
        # Append new emails
        existing = set(lead_data.get('email', '').split('; '))
        new_emails = set(result['emails']) - existing
        if new_emails:
            all_emails = list(existing | new_emails)
            lead_data['email'] = '; '.join([e for e in all_emails if e])
            updated = True

    # Add phones if lead doesn't have one
    if not lead_data.get('phone') and result.get('phones'):
        lead_data['phone'] = '; '.join(result['phones'])
        updated = True
    elif result.get('phones'):
        # Append new phones
        existing = set(lead_data.get('phone', '').split('; '))
        new_phones = set(result['phones']) - existing
        if new_phones:
            all_phones = list(existing | new_phones)
            lead_data['phone'] = '; '.join([p for p in all_phones if p])
            updated = True

    # Add WhatsApp
    if result.get('whatsapp'):
        if 'scraped_data' not in lead_data:
            lead_data['scraped_data'] = {}
        lead_data['scraped_data']['whatsapp'] = result['whatsapp']
        updated = True

    # Add social links
    if result.get('social'):
        if 'scraped_data' not in lead_data:
            lead_data['scraped_data'] = {}
        lead_data['scraped_data']['social_links'] = result['social']
        updated = True

    # Mark as enriched
    if 'scraped_data' not in lead_data:
        lead_data['scraped_data'] = {}
    lead_data['scraped_data']['website_enriched'] = True
    lead_data['scraped_data']['pages_checked'] = result.get('pages_checked', 1)

    return {
        'success': True,
        'updated': updated,
        'emails_found': len(result.get('emails', [])),
        'phones_found': len(result.get('phones', [])),
        'lead': lead_data
    }
