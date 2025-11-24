"""
Enhanced LinkedIn Profile Scraper
Uses SERPAPI to find LinkedIn profiles and extract contact information and KPIs
"""

import os
import time
from typing import List, Dict, Optional
import logging
import re

logger = logging.getLogger(__name__)

SERPAPI_KEY = os.getenv('SERPAPI_KEY')


class LinkedInScraperError(Exception):
    """Custom exception for LinkedIn scraper errors"""
    pass


class LinkedInContactExtractor:
    """Extract contact information from LinkedIn profiles"""

    def __init__(self):
        # Email patterns
        self.email_patterns = [
            re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            re.compile(r'(?:email|mail|contact)[\s:]*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})', re.IGNORECASE),
        ]

        # Phone patterns
        self.phone_patterns = [
            re.compile(r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),
            re.compile(r'(\+\d{1,4}[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}'),
            re.compile(r'\+971[\s-]?\d{1,2}[\s-]?\d{3}[\s-]?\d{4}'),
        ]

        # Website patterns
        self.website_patterns = [
            re.compile(r'(https?://[^\s<>"{}|\\^`\[\]]+)', re.IGNORECASE),
            re.compile(r'\b([a-zA-Z0-9-]+\.(?:com|net|org|io|co|ae|eg|sa))\b', re.IGNORECASE),
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
        skip_domains = ['example.com', 'test.com', 'placeholder.com', 'linkedin.com']
        skip_keywords = ['noreply', 'no-reply', 'donotreply']

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
                digits = re.sub(r'\D', '', phone)
                if len(digits) >= 9:
                    phones.add(phone)

        return list(phones)

    def extract_website(self, text: str) -> Optional[str]:
        if not text:
            return None

        for pattern in self.website_patterns:
            match = pattern.search(text)
            if match:
                url = match.group(1) if match.lastindex else match.group(0)
                # Skip social media links
                if any(social in url.lower() for social in ['linkedin', 'facebook', 'twitter', 'instagram']):
                    continue
                if not url.startswith('http'):
                    url = f'https://{url}'
                return url
        return None


class LinkedInKPIExtractor:
    """Extract KPIs from LinkedIn profiles"""

    def __init__(self):
        self.connections_patterns = [
            re.compile(r'([\d,]+)\+?\s*(?:connections|Connections)', re.IGNORECASE),
            re.compile(r'(?:connections|Connections)[\s:]*(\d+)', re.IGNORECASE),
        ]

        self.followers_patterns = [
            re.compile(r'([\d,.]+[KkMm]?)\s*(?:followers|Followers)', re.IGNORECASE),
        ]

        self.experience_patterns = [
            re.compile(r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:experience|exp)?', re.IGNORECASE),
        ]

    def parse_number(self, value: str) -> int:
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

    def extract_connections(self, text: str) -> int:
        if not text:
            return 0

        for pattern in self.connections_patterns:
            match = pattern.search(text)
            if match:
                return self.parse_number(match.group(1))
        return 0

    def extract_followers(self, text: str) -> int:
        if not text:
            return 0

        for pattern in self.followers_patterns:
            match = pattern.search(text)
            if match:
                return self.parse_number(match.group(1))
        return 0

    def extract_experience_years(self, text: str) -> int:
        if not text:
            return 0

        for pattern in self.experience_patterns:
            match = pattern.search(text)
            if match:
                return int(match.group(1))
        return 0

    def estimate_seniority(self, title: str, experience: int) -> str:
        """Estimate seniority level from job title and experience"""
        title_lower = title.lower()

        senior_keywords = ['ceo', 'cto', 'cfo', 'coo', 'chief', 'president', 'vp', 'vice president',
                         'director', 'head of', 'partner', 'founder', 'owner']
        mid_keywords = ['manager', 'lead', 'senior', 'sr.', 'principal']
        junior_keywords = ['junior', 'jr.', 'associate', 'assistant', 'intern', 'trainee']

        for keyword in senior_keywords:
            if keyword in title_lower:
                return "Executive/Senior"

        for keyword in mid_keywords:
            if keyword in title_lower:
                return "Mid-Level"

        for keyword in junior_keywords:
            if keyword in title_lower:
                return "Entry-Level"

        # Fallback to experience-based estimation
        if experience >= 10:
            return "Senior"
        elif experience >= 5:
            return "Mid-Level"
        elif experience > 0:
            return "Entry-Level"

        return "Unknown"


contact_extractor = LinkedInContactExtractor()
kpi_extractor = LinkedInKPIExtractor()


def search_linkedin_profiles(
    query: str,
    max_results: int = 30
) -> List[Dict]:
    """
    Search for LinkedIn profiles using SERPAPI with enhanced data extraction

    Args:
        query: Search query (e.g., "marketing manager Dubai")
        max_results: Maximum number of results (default 30)

    Returns:
        List of profile dictionaries with professional information and KPIs
    """
    if not SERPAPI_KEY or SERPAPI_KEY == 'your-serpapi-key':
        logger.warning("SERPAPI key not configured, returning mock data")
        return _get_mock_data(query, max_results)

    try:
        from serpapi import GoogleSearch
    except ImportError:
        logger.error("serpapi package not installed")
        raise LinkedInScraperError("serpapi package not installed. Run: pip install google-search-results")

    results = []
    seen_urls = set()

    # Multiple search queries for better coverage
    search_queries = [
        f'site:linkedin.com/in {query}',
        f'site:linkedin.com/in {query} email contact',
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

                # Only include personal profiles (linkedin.com/in/)
                if 'linkedin.com/in/' not in url:
                    continue

                # Skip company pages
                if '/company/' in url or '/jobs/' in url or '/posts/' in url:
                    continue

                if url in seen_urls:
                    continue

                profile_data = _extract_profile_data(url, result)
                if profile_data:
                    results.append(profile_data)
                    seen_urls.add(url)

            time.sleep(0.5)

        except Exception as e:
            logger.error(f"SERPAPI search failed for query '{gquery}': {e}")
            continue

    logger.info(f"Found {len(results)} LinkedIn profiles for query: {query}")
    return results


def _extract_profile_data(url: str, serpapi_result: Dict) -> Dict:
    """Extract comprehensive profile data from SERPAPI result"""

    title = serpapi_result.get("title", "")
    snippet = serpapi_result.get("snippet", "")
    rich_snippet = serpapi_result.get("rich_snippet", {})

    # Combine all text sources
    full_text = f"{title} {snippet}"

    if rich_snippet:
        extensions = rich_snippet.get("extensions", [])
        if extensions:
            full_text += " " + " ".join(extensions)

    # Extract username from URL
    username = url.rstrip('/').split('/in/')[-1].split('?')[0] if '/in/' in url else ''

    # Parse name and title from search result title
    # LinkedIn titles are usually: "Name - Title - Company | LinkedIn"
    name = ""
    job_title = ""
    company = ""

    if ' - ' in title:
        parts = title.replace(' | LinkedIn', '').split(' - ')
        name = parts[0].strip()
        if len(parts) > 1:
            job_title = parts[1].strip()
        if len(parts) > 2:
            company = parts[2].strip()
    elif '|' in title:
        name = title.split('|')[0].strip()
    else:
        name = title.replace(' | LinkedIn', '').strip()

    # Extract contact information
    emails = contact_extractor.extract_emails(full_text)
    phones = contact_extractor.extract_phones(full_text)
    website = contact_extractor.extract_website(full_text)

    # Extract KPIs
    connections = kpi_extractor.extract_connections(full_text)
    followers = kpi_extractor.extract_followers(full_text)
    experience_years = kpi_extractor.extract_experience_years(full_text)
    seniority = kpi_extractor.estimate_seniority(job_title, experience_years)

    # Extract location from snippet
    location = _extract_location(snippet)

    # Determine industry/category
    industry = _detect_industry(full_text, job_title)

    # Clean bio from snippet
    bio = snippet[:500] if snippet else ""

    return {
        'title': name,
        'username': username,
        'url': url,
        'job_title': job_title,
        'company': company,
        'location': location,
        'website': website or "",
        'email': "; ".join(emails) if emails else "",
        'phone': "; ".join(phones) if phones else "",
        'bio': bio,
        'connections': connections,
        'connections_display': _format_number(connections),
        'followers': followers,
        'followers_display': _format_number(followers),
        'experience_years': experience_years,
        'seniority': seniority,
        'industry': industry,
        'source': 'linkedin',
        'has_contact': bool(emails or phones or website),
    }


def _extract_location(text: str) -> str:
    """Extract location from LinkedIn snippet"""
    # Common patterns in LinkedIn snippets
    location_patterns = [
        re.compile(r'(?:Location|Based in|Located in)[\s:]*([^.·\-]+)', re.IGNORECASE),
        re.compile(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2,})', re.IGNORECASE),  # City, Country/State
    ]

    for pattern in location_patterns:
        match = pattern.search(text)
        if match:
            return match.group(1).strip()

    # Common locations in UAE/Middle East
    locations = ['Dubai', 'Abu Dhabi', 'Sharjah', 'UAE', 'United Arab Emirates',
                 'Saudi Arabia', 'Qatar', 'Kuwait', 'Bahrain', 'Oman', 'Egypt', 'Cairo']
    for loc in locations:
        if loc.lower() in text.lower():
            return loc

    return ""


def _detect_industry(text: str, job_title: str) -> str:
    """Detect industry from profile content"""
    text_lower = (text + " " + job_title).lower()

    industries = {
        'Technology': ['software', 'developer', 'engineer', 'tech', 'IT', 'programming', 'data', 'cloud', 'AI'],
        'Finance & Banking': ['finance', 'banking', 'investment', 'accounting', 'financial', 'analyst'],
        'Marketing & Sales': ['marketing', 'sales', 'digital marketing', 'brand', 'advertising', 'growth'],
        'Healthcare': ['healthcare', 'medical', 'doctor', 'nurse', 'pharma', 'hospital', 'health'],
        'Real Estate': ['real estate', 'property', 'broker', 'realtor', 'construction'],
        'Education': ['education', 'teacher', 'professor', 'training', 'academic', 'university'],
        'Consulting': ['consultant', 'consulting', 'advisory', 'strategy'],
        'Legal': ['lawyer', 'attorney', 'legal', 'law firm', 'advocate'],
        'HR & Recruitment': ['HR', 'human resources', 'recruiter', 'recruitment', 'talent'],
        'Operations': ['operations', 'logistics', 'supply chain', 'procurement'],
        'Design & Creative': ['design', 'creative', 'UX', 'UI', 'graphic', 'art director'],
        'Media & Entertainment': ['media', 'journalist', 'content', 'entertainment', 'production'],
    }

    for industry, keywords in industries.items():
        if any(kw.lower() in text_lower for kw in keywords):
            return industry

    return 'Professional Services'


def _format_number(num: int) -> str:
    """Format number for display"""
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
    industries = ['Technology', 'Finance & Banking', 'Marketing & Sales',
                  'Healthcare', 'Consulting', 'Real Estate']
    titles = ['Manager', 'Director', 'Senior Specialist', 'Lead', 'Consultant', 'Analyst']
    companies = ['Tech Corp', 'Global Finance Ltd', 'Marketing Pro', 'Health Systems', 'ConsultCo', 'Property Group']
    locations = ['Dubai, UAE', 'Abu Dhabi, UAE', 'Riyadh, Saudi Arabia', 'Cairo, Egypt', 'Doha, Qatar']

    mock_results = []
    for i in range(min(max_results, 10)):
        industry = industries[i % len(industries)]
        job_title = f"{titles[i % len(titles)]} - {industry.split()[0]}"
        company = companies[i % len(companies)]
        location = locations[i % len(locations)]
        connections = 500 + i * 100
        experience = 3 + (i % 10)

        first_names = ['Ahmed', 'Mohammed', 'Sara', 'Fatima', 'Omar', 'Layla', 'Khalid', 'Noura', 'Ali', 'Maryam']
        last_names = ['Al-Hassan', 'Khan', 'Smith', 'Johnson', 'Al-Ali', 'Rahman', 'Patel', 'Williams', 'Ahmed', 'Singh']

        name = f"{first_names[i % len(first_names)]} {last_names[i % len(last_names)]}"
        username = name.lower().replace(' ', '-')

        mock_results.append({
            'title': name,
            'username': username,
            'url': f"https://linkedin.com/in/{username}",
            'job_title': job_title,
            'company': company,
            'location': location,
            'website': f"https://{username.replace('-', '')}.com" if i % 3 == 0 else "",
            'email': f"{username.replace('-', '.')}@{company.lower().replace(' ', '')}.com" if i % 2 == 0 else "",
            'phone': f"+971 50 {100+i:03d} {1000+i*10:04d}" if i % 3 == 0 else "",
            'bio': f"{job_title} at {company}. {experience}+ years of experience in {industry}. Based in {location}.",
            'connections': connections,
            'connections_display': _format_number(connections),
            'followers': int(connections * 1.5),
            'followers_display': _format_number(int(connections * 1.5)),
            'experience_years': experience,
            'seniority': kpi_extractor.estimate_seniority(job_title, experience),
            'industry': industry,
            'source': 'linkedin',
            'has_contact': i % 2 == 0,
        })

    return mock_results
