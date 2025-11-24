import os
import time
import pandas as pd
import googlemaps
from dotenv import load_dotenv

load_dotenv()

def collect_google_leads(query, max_results):
    """Simple Google Maps lead collection"""
    try:
        # Initialize Google Maps
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("GOOGLE_API_KEY not found")
            return create_sample_file(query)

        gmaps = googlemaps.Client(key=api_key)

        # Search for places
        print(f"Searching for: {query}")
        results = gmaps.places(query=query)

        if 'results' not in results:
            print("No results found")
            return create_sample_file(query)

        places = results['results'][:max_results]
        print(f"Processing {len(places)} places")

        # Process each place
        leads_data = []
        for place in places:
            try:
                # Get basic info
                name = place.get('name', 'Unknown')
                place_id = place.get('place_id', '')

                # Get detailed info
                details = {}
                if place_id:
                    try:
                        detail_result = gmaps.place(
                            place_id=place_id,
                            fields=['name', 'formatted_address', 'formatted_phone_number', 'website']
                        )
                        details = detail_result.get('result', {})
                    except:
                        pass

                # Create lead entry
                lead = {
                    'Title': details.get('name', name),
                    'Address': details.get('formatted_address', ''),
                    'Phone': details.get('formatted_phone_number', ''),
                    'Website': details.get('website', ''),
                    'Email': ''  # Will be populated later if needed
                }

                leads_data.append(lead)
                print(f"Processed: {lead['Title']}")

            except Exception as e:
                print(f"Error processing place: {e}")
                continue

        # Create Excel file
        if leads_data:
            df = pd.DataFrame(leads_data)
            filename = f"google_maps_leads_{int(time.time())}.xlsx"
            df.to_excel(filename, index=False)
            print(f"Success! Created {filename} with {len(leads_data)} leads")
            return filename
        else:
            return create_sample_file(query)

    except Exception as e:
        print(f"Error: {e}")
        return create_sample_file(query)

def create_sample_file(query):
    """Create sample file when API fails"""
    sample_data = [{
        'Title': f'Sample Business for: {query}',
        'Address': '123 Main St, Sample City',
        'Phone': '+1-555-0123',
        'Website': 'https://example.com',
        'Email': 'contact@example.com'
    }]

    df = pd.DataFrame(sample_data)
    filename = f"sample_leads_{int(time.time())}.xlsx"
    df.to_excel(filename, index=False)
    print(f"Created sample file: {filename}")
    return filename

if __name__ == "__main__":
    result = collect_google_leads("coffee shops", 3)
    print(f"Result: {result}")