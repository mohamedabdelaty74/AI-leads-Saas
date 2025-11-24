"""
Enhanced Instagram Profile Scraper
Uses SERPAPI to find Instagram profiles and extract maximum contact information and KPIs
"""

import os
import time
import requests
from typing import List, Dict, Optional
import logging
import re

logger = logging.getLogger(__name__)

SERPAPI_KEY = os.getenv('SERPAPI_KEY')


class InstagramScraperError(Exception):
    """Custom exception for Instagram scraper errors"""
    pass


class EnhancedContactExtractor:
    """Advanced contact extractor with multiple patterns for better accuracy"""

    def __init__(self):
        # Email patterns - more comprehensive
        self.email_patterns = [
            re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            re.compile(r'(?:email|mail|contact|dm)[\s:]*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})', re.IGNORECASE),
        ]

        # Phone patterns - international formats
        self.phone_patterns = [
            re.compile(r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),
            re.compile(r'(\+\d{1,4}[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}'),
            re.compile(r'(?:phone|tel|call|whatsapp|wa)[\s:]*(\+?[\d\s\-().]{10,})', re.IGNORECASE),
            # UAE/Middle East formats
            re.compile(r'\+971[\s-]?\d{1,2}[\s-]?\d{3}[\s-]?\d{4}'),
            re.compile(r'0\d{1,2}[\s-]?\d{3}[\s-]?\d{4}'),
        ]

        # WhatsApp pattern
        self.whatsapp_pattern = re.compile(r'(?:whatsapp|wa|wa\.me)[\s:/]*(\+?[\d\s\-]{10,})', re.IGNORECASE)

        # Website patterns
        self.website_patterns = [
            re.compile(r'(?:website|site|link|www)[\s:]*([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', re.IGNORECASE),
            re.compile(r'(https?://[^\s<>"{}|\\^`\[\]]+)', re.IGNORECASE),
            re.compile(r'\b([a-zA-Z0-9-]+\.(?:com|net|org|io|co|shop|store|ae|eg|sa))\b', re.IGNORECASE),
        ]

    def extract_emails(self, text: str) -> List[str]:
        if not text:
            return []

        emails = set()
        for pattern in self.email_patterns:
            matches = pattern.findall(text.lower())
            for match in matches:
                email = match if isinstance(match, str) else match[0] if match else ''
                if email and self._is_valid_email(email):
                    emails.add(email)

        return list(emails)

    def _is_valid_email(self, email: str) -> bool:
        skip_domains = ['example.com', 'test.com', 'placeholder.com', 'domain.com', 'email.com']
        skip_keywords = ['noreply', 'no-reply', 'donotreply', 'mailer-daemon']

        if '@' not in email:
            return False

        domain = email.split('@')[1]
        if domain in skip_domains:
            return False

        for keyword in skip_keywords:
            if keyword in email:
                return False

        return True

    def extract_phones(self, text: str) -> List[str]:
        if not text:
            return []

        phones = set()
        for pattern in self.phone_patterns:
            matches = pattern.findall(text)
            for match in matches:
                phone = match if isinstance(match, str) else ''.join(match) if match else ''
                phone = phone.strip()
                # Clean and validate
                digits = re.sub(r'\D', '', phone)
                if len(digits) >= 9:  # At least 9 digits for international
                    phones.add(phone)

        return list(phones)

    def extract_whatsapp(self, text: str) -> Optional[str]:
        if not text:
            return None

        match = self.whatsapp_pattern.search(text)
        if match:
            number = match.group(1).strip()
            digits = re.sub(r'\D', '', number)
            if len(digits) >= 10:
                return number
        return None

    def extract_website(self, text: str) -> Optional[str]:
        if not text:
            return None

        for pattern in self.website_patterns:
            match = pattern.search(text)
            if match:
                url = match.group(1) if match.lastindex else match.group(0)
                # Skip social media links
                if any(social in url.lower() for social in ['instagram', 'facebook', 'twitter', 'tiktok', 'youtube']):
                    continue
                # Add https if missing
                if not url.startswith('http'):
                    url = f'https://{url}'
                return url
        return None


class KPIExtractor:
    """Extract KPIs like followers, posts, engagement from Instagram data"""

    def __init__(self):
        self.follower_patterns = [
            re.compile(r'([\d,.]+[KkMm]?)\s*(?:followers|Followers)', re.IGNORECASE),
            re.compile(r'(?:followers|Followers)[\s:]*([[\d,.]+[KkMm]?)', re.IGNORECASE),
        ]

        self.following_patterns = [
            re.compile(r'([\d,.]+[KkMm]?)\s*(?:following|Following)', re.IGNORECASE),
        ]

        self.posts_patterns = [
            re.compile(r'([\d,.]+[KkMm]?)\s*(?:posts|Posts)', re.IGNORECASE),
        ]

    def parse_number(self, value: str) -> int:
        """Convert string like '10.5K' or '1.2M' to integer"""
        if not value:
            return 0

        value = value.replace(',', '').strip()
        multiplier = 1

        if value.endswith('K') or value.endswith('k'):
            multiplier = 1000
            value = value[:-1]
        elif value.endswith('M') or value.endswith('m'):
            multiplier = 1000000
            value = value[:-1]

        try:
            return int(float(value) * multiplier)
        except:
            return 0

    def extract_followers(self, text: str) -> int:
        if not text:
            return 0

        for pattern in self.follower_patterns:
            match = pattern.search(text)
            if match:
                return self.parse_number(match.group(1))
        return 0

    def extract_following(self, text: str) -> int:
        if not text:
            return 0

        for pattern in self.following_patterns:
            match = pattern.search(text)
            if match:
                return self.parse_number(match.group(1))
        return 0

    def extract_posts(self, text: str) -> int:
        if not text:
            return 0

        for pattern in self.posts_patterns:
            match = pattern.search(text)
            if match:
                return self.parse_number(match.group(1))
        return 0

    def estimate_engagement_rate(self, followers: int) -> str:
        """Estimate engagement rate category based on follower count"""
        if followers == 0:
            return "Unknown"
        elif followers < 1000:
            return "Nano (High Engagement)"
        elif followers < 10000:
            return "Micro (Good Engagement)"
        elif followers < 100000:
            return "Mid-tier (Moderate)"
        elif followers < 1000000:
            return "Macro (Lower Engagement)"
        else:
            return "Mega (Variable)"


contact_extractor = EnhancedContactExtractor()
kpi_extractor = KPIExtractor()


def search_instagram_profiles(
    query: str,
    max_results: int = 30
) -> List[Dict]:
    """
    Search for Instagram profiles using SERPAPI with enhanced data extraction

    Args:
        query: Search query (e.g., "restaurants Dubai")
        max_results: Maximum number of results (default 30)

    Returns:
        List of profile dictionaries with business information and KPIs
    """
    if not SERPAPI_KEY or SERPAPI_KEY == 'your-serpapi-key':
        logger.warning("SERPAPI key not configured, returning mock data")
        return _get_mock_data(query, max_results)

    try:
        from serpapi import GoogleSearch
    except ImportError:
        logger.error("serpapi package not installed")
        raise InstagramScraperError("serpapi package not installed. Run: pip install google-search-results")

    results = []
    seen_urls = set()

    # Multiple search queries for better coverage
    search_queries = [
        f'site:instagram.com {query}',
        f'site:instagram.com {query} email contact',
        f'site:instagram.com {query} phone whatsapp',
    ]

    for gquery in search_queries:
        if len(results) >= max_results:
            break

        search_params = {
            "engine": "google",
            "q": gquery,
            "api_key": SERPAPI_KEY,
            "num": min(100, max_results * 2)
        }

        try:
            search = GoogleSearch(search_params)
            data = search.get_dict()
            organic_results = data.get("organic_results", [])

            for result in organic_results:
                if len(results) >= max_results:
                    break

                url = result.get("link", "")

                # Skip non-profile URLs (posts, reels, etc.)
                if 'instagram.com/' not in url:
                    continue
                if any(x in url for x in ['/p/', '/tv/', '/reel/', '/stories/', '/explore/', '/tags/']):
                    continue

                if url in seen_urls:
                    continue

                profile_data = _extract_profile_data(url, result)
                if profile_data:
                    results.append(profile_data)
                    seen_urls.add(url)

            # Small delay between searches
            time.sleep(0.5)

        except Exception as e:
            logger.error(f"SERPAPI search failed for query '{gquery}': {e}")
            continue

    logger.info(f"Found {len(results)} Instagram profiles for query: {query}")
    return results


def _extract_profile_data(url: str, serpapi_result: Dict) -> Dict:
    """Extract comprehensive profile data from SERPAPI result"""

    # Get all text content for extraction
    title = serpapi_result.get("title", "")
    snippet = serpapi_result.get("snippet", "")
    rich_snippet = serpapi_result.get("rich_snippet", {})

    # Combine all text sources
    full_text = f"{title} {snippet}"

    # Add rich snippet data if available
    if rich_snippet:
        extensions = rich_snippet.get("extensions", [])
        if extensions:
            full_text += " " + " ".join(extensions)

        top = rich_snippet.get("top", {})
        if top:
            detected_extensions = top.get("detected_extensions", {})
            full_text += " " + " ".join(str(v) for v in detected_extensions.values())

    # Extract username from URL
    username = url.rstrip('/').split('/')[-1]
    if username.startswith('@'):
        username = username[1:]

    # Parse title for profile name
    profile_name = title
    if '(' in title:
        profile_name = title.split('(')[0].strip()
    elif '•' in title:
        profile_name = title.split('•')[0].strip()
    elif '-' in title:
        profile_name = title.split('-')[0].strip()

    # If profile name is just "Instagram", use username
    if profile_name.lower() in ['instagram', '']:
        profile_name = username

    # Extract contact information
    emails = contact_extractor.extract_emails(full_text)
    phones = contact_extractor.extract_phones(full_text)
    whatsapp = contact_extractor.extract_whatsapp(full_text)
    website = contact_extractor.extract_website(full_text)

    # Extract KPIs
    followers = kpi_extractor.extract_followers(full_text)
    following = kpi_extractor.extract_following(full_text)
    posts = kpi_extractor.extract_posts(full_text)
    engagement_category = kpi_extractor.estimate_engagement_rate(followers)

    # Extract bio from snippet
    bio = snippet
    # Clean up bio - remove follower counts and generic text
    bio_clean = re.sub(r'[\d,.]+[KkMm]?\s*(?:Followers|Following|Posts)', '', bio)
    bio_clean = re.sub(r'\s+', ' ', bio_clean).strip()

    # Determine business category from content
    category = _detect_category(full_text, username)

    return {
        'title': profile_name,
        'username': f"@{username}",
        'url': url,
        'website': website or "",
        'email': "; ".join(emails) if emails else "",
        'phone': "; ".join(phones) if phones else "",
        'whatsapp': whatsapp or (phones[0] if phones else ""),
        'bio': bio_clean[:500] if bio_clean else "",
        'followers': followers,
        'followers_display': _format_number(followers),
        'following': following,
        'posts': posts,
        'engagement_category': engagement_category,
        'category': category,
        'source': 'instagram',
        'has_contact': bool(emails or phones or whatsapp or website),
    }


def _detect_category(text: str, username: str) -> str:
    """Detect business category from profile content"""
    text_lower = text.lower() + " " + username.lower()

    categories = {
        'Fashion & Clothing': ['fashion', 'clothing', 'clothes', 'wear', 'style', 'boutique', 'dress', 'apparel'],
        'Food & Restaurant': ['food', 'restaurant', 'cafe', 'coffee', 'eat', 'kitchen', 'chef', 'bakery', 'sweet'],
        'Beauty & Cosmetics': ['beauty', 'makeup', 'cosmetic', 'skincare', 'salon', 'spa', 'nail', 'hair'],
        'Health & Fitness': ['fitness', 'gym', 'health', 'workout', 'yoga', 'trainer', 'nutrition', 'wellness'],
        'Technology': ['tech', 'software', 'digital', 'app', 'developer', 'coding', 'startup'],
        'Real Estate': ['real estate', 'property', 'home', 'apartment', 'villa', 'realty'],
        'Travel & Tourism': ['travel', 'tour', 'hotel', 'vacation', 'trip', 'adventure'],
        'E-commerce & Retail': ['shop', 'store', 'buy', 'sell', 'online', 'retail', 'delivery'],
        'Photography & Art': ['photo', 'art', 'design', 'creative', 'studio', 'gallery'],
        'Education': ['education', 'school', 'learn', 'course', 'training', 'academy', 'tutor'],
        'Services': ['service', 'consulting', 'agency', 'solutions', 'professional'],
    }

    for category, keywords in categories.items():
        if any(kw in text_lower for kw in keywords):
            return category

    return 'Business'


def _format_number(num: int) -> str:
    """Format number for display (e.g., 10500 -> '10.5K')"""
    if num == 0:
        return ""
    elif num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    else:
        return str(num)


def _get_mock_data(query: str, max_results: int) -> List[Dict]:
    """Return realistic mock data when SERPAPI key is not configured"""
    categories = ['Fashion & Clothing', 'Food & Restaurant', 'Beauty & Cosmetics',
                  'Health & Fitness', 'E-commerce & Retail', 'Services']

    mock_results = []
    for i in range(min(max_results, 10)):
        category = categories[i % len(categories)]
        username = f"{query.replace(' ', '').lower()}_{i+1}"
        followers = (i + 1) * 1500

        mock_results.append({
            'title': f"{query.title()} {category.split()[0]} #{i+1}",
            'username': f"@{username}",
            'url': f"https://instagram.com/{username}",
            'website': f"https://{username}.com" if i % 3 == 0 else "",
            'email': f"contact@{username}.com" if i % 2 == 0 else "",
            'phone': f"+971 50 {100+i:03d} {1000+i*10:04d}" if i % 3 == 0 else "",
            'whatsapp': f"+971 50 {100+i:03d} {1000+i*10:04d}" if i % 4 == 0 else "",
            'bio': f"Professional {category.lower()} in {query}. Quality products & services. DM for inquiries!",
            'followers': followers,
            'followers_display': _format_number(followers),
            'following': int(followers * 0.3),
            'posts': 50 + i * 20,
            'engagement_category': kpi_extractor.estimate_engagement_rate(followers),
            'category': category,
            'source': 'instagram',
            'has_contact': i % 2 == 0,
        })

    return mock_results
