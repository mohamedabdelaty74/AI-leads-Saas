"""
Google Maps Places API Integration
Real lead scraping from Google Maps
"""

import os
import requests
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
PLACES_API_URL = "https://maps.googleapis.com/maps/api/place"


class GoogleMapsScraperError(Exception):
    """Custom exception for Google Maps scraper errors"""
    pass


def search_places(
    query: str,
    location: str = "",
    max_results: int = 50
) -> List[Dict]:
    """
    Search for places using Google Maps Places API

    Args:
        query: Search query (e.g., "restaurants in Dubai")
        location: Location to search (optional, can be in query)
        max_results: Maximum number of results (default 50, max 60)

    Returns:
        List of place dictionaries with business information
    """
    if not GOOGLE_API_KEY or GOOGLE_API_KEY == 'your-google-api-key':
        logger.warning("Google API key not configured, returning mock data")
        return _get_mock_data(query, location, max_results)

    try:
        # Combine query and location
        search_query = f"{query} {location}".strip()

        # Text Search API endpoint
        url = f"{PLACES_API_URL}/textsearch/json"

        all_results = []
        next_page_token = None

        # Google Places API returns max 20 results per page
        # We need to paginate to get more results
        while len(all_results) < max_results:
            params = {
                'query': search_query,
                'key': GOOGLE_API_KEY,
            }

            if next_page_token:
                params['pagetoken'] = next_page_token

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get('status') != 'OK':
                if data.get('status') == 'ZERO_RESULTS':
                    logger.info(f"No results found for query: {search_query}")
                    break
                else:
                    raise GoogleMapsScraperError(
                        f"Google Places API error: {data.get('status')} - {data.get('error_message', 'Unknown error')}"
                    )

            results = data.get('results', [])

            # Process each place and get details
            for place in results:
                if len(all_results) >= max_results:
                    break

                place_details = _get_place_details(place['place_id'])
                if place_details:
                    all_results.append(place_details)

            # Check for next page
            next_page_token = data.get('next_page_token')
            if not next_page_token or len(all_results) >= max_results:
                break

            # Need to wait a bit before requesting next page (Google's requirement)
            import time
            time.sleep(2)

        logger.info(f"Found {len(all_results)} places for query: {search_query}")
        return all_results[:max_results]

    except requests.RequestException as e:
        logger.error(f"Error calling Google Places API: {e}")
        raise GoogleMapsScraperError(f"Failed to fetch places: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in Google Maps scraper: {e}")
        raise GoogleMapsScraperError(f"Scraping failed: {str(e)}")


def _get_place_details(place_id: str) -> Optional[Dict]:
    """
    Get detailed information about a place

    Args:
        place_id: Google Place ID

    Returns:
        Dictionary with place details
    """
    try:
        url = f"{PLACES_API_URL}/details/json"
        params = {
            'place_id': place_id,
            'fields': 'name,formatted_address,formatted_phone_number,website,rating,user_ratings_total,types,geometry',
            'key': GOOGLE_API_KEY
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get('status') != 'OK':
            logger.warning(f"Could not get details for place {place_id}: {data.get('status')}")
            return None

        result = data.get('result', {})

        # Extract and format the data
        return {
            'title': result.get('name', ''),
            'address': result.get('formatted_address', ''),
            'phone': result.get('formatted_phone_number', ''),
            'website': result.get('website', ''),
            'rating': result.get('rating', 0),
            'reviews_count': result.get('user_ratings_total', 0),
            'category': ', '.join(result.get('types', [])[:3]) if result.get('types') else '',
            'latitude': result.get('geometry', {}).get('location', {}).get('lat'),
            'longitude': result.get('geometry', {}).get('location', {}).get('lng'),
        }

    except Exception as e:
        logger.error(f"Error getting place details for {place_id}: {e}")
        return None


def _get_mock_data(query: str, location: str, max_results: int) -> List[Dict]:
    """
    Return mock data when API key is not configured
    For development and testing purposes
    """
    logger.info(f"Returning mock data for query: {query} in {location}")

    search_term = f"{query} {location}".strip()

    mock_leads = []
    for i in range(min(max_results, 10)):  # Return max 10 mock results
        mock_leads.append({
            'title': f"{query.title()} Business #{i+1}",
            'address': f"{i+1} Main Street, {location or 'Downtown'}",
            'phone': f"+1-555-{1000 + i:04d}",
            'website': f"https://business{i+1}.example.com",
            'rating': round(3.5 + (i % 20) / 10, 1),
            'reviews_count': 50 + (i * 15),
            'category': query.title(),
            'latitude': 25.2048 + (i * 0.01),
            'longitude': 55.2708 + (i * 0.01),
        })

    return mock_leads


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("Testing Google Maps Scraper...")
    print("=" * 60)

    try:
        results = search_places(
            query="restaurants",
            location="Dubai Marina",
            max_results=5
        )

        print(f"\nFound {len(results)} results:")
        for i, place in enumerate(results, 1):
            print(f"\n{i}. {place['title']}")
            print(f"   Address: {place['address']}")
            print(f"   Phone: {place['phone']}")
            print(f"   Rating: {place['rating']} ({place['reviews_count']} reviews)")

    except GoogleMapsScraperError as e:
        print(f"\nError: {e}")
