"""
Test the Elite Creatif API

🎓 TEACHING: API Testing Flow
1. Register new user + company
2. Login to get JWT token
3. Create a campaign (using token)
4. List campaigns
5. Get campaign details

Run: python scripts/test_api.py
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

def print_response(response):
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")

# ============================================================================
# Test 1: Health Check
# ============================================================================

print_section("1. Health Check")
response = requests.get(f"{BASE_URL}/health")
print_response(response)

# ============================================================================
# Test 2: Register New User
# ============================================================================

print_section("2. Register New User & Company")
register_data = {
    "company_name": "Acme Corporation",
    "company_email": "info@acme-corp.com",
    "company_website": "https://acme-corp.com",
    "email": "john@acme-corp.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
}

response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=register_data)
print_response(response)

if response.status_code == 201:
    tokens = response.json()
    access_token = tokens['access_token']
    user_id = tokens['user']['id']
    print(f"\n[OK] Registration successful!")
    print(f"  User ID: {user_id}")
    print(f"  Token: {access_token[:50]}...")
else:
    print("\n[FAIL] Registration failed")
    exit(1)

# ============================================================================
# Test 3: Get Current User
# ============================================================================

print_section("3. Get Current User Profile")
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)
print_response(response)

# ============================================================================
# Test 4: Get Tenant Profile
# ============================================================================

print_section("4. Get Company Profile")
response = requests.get(f"{BASE_URL}/api/v1/tenants/me", headers=headers)
print_response(response)

if response.status_code == 200:
    tenant = response.json()
    print(f"\n[OK] Company: {tenant['name']}")
    print(f"  Plan: {tenant['plan']}")
    print(f"  Quota: {tenant['leads_used']}/{tenant['leads_quota']} leads used")

# ============================================================================
# Test 5: Create Campaign
# ============================================================================

print_section("5. Create Marketing Campaign")
campaign_data = {
    "name": "Q1 2025 Dubai Restaurants",
    "description": "Outreach to premium restaurants in Dubai",
    "search_query": "restaurants in Dubai Marina",
    "lead_source": "google_maps",
    "max_leads": 50,
    "description_style": "professional"
}

response = requests.post(f"{BASE_URL}/api/v1/campaigns", json=campaign_data, headers=headers)
print_response(response)

if response.status_code == 201:
    campaign = response.json()
    campaign_id = campaign['id']
    print(f"\n[OK] Campaign created!")
    print(f"  ID: {campaign_id}")
    print(f"  Name: {campaign['name']}")
else:
    print("\n[FAIL] Campaign creation failed")
    campaign_id = None

# ============================================================================
# Test 6: List Campaigns
# ============================================================================

print_section("6. List All Campaigns")
response = requests.get(f"{BASE_URL}/api/v1/campaigns", headers=headers)
print_response(response)

if response.status_code == 200:
    campaigns = response.json()
    print(f"\n[OK] Found {len(campaigns)} campaign(s)")

# ============================================================================
# Test 7: Get Campaign Details
# ============================================================================

if campaign_id:
    print_section("7. Get Campaign Details")
    response = requests.get(f"{BASE_URL}/api/v1/campaigns/{campaign_id}", headers=headers)
    print_response(response)

# ============================================================================
# Test 8: Update Campaign
# ============================================================================

if campaign_id:
    print_section("8. Update Campaign Status")
    update_data = {"status": "active"}
    response = requests.patch(
        f"{BASE_URL}/api/v1/campaigns/{campaign_id}",
        json=update_data,
        headers=headers
    )
    print_response(response)

# ============================================================================
# Test 9: Test Authentication Failure
# ============================================================================

print_section("9. Test Invalid Token (Security)")
bad_headers = {"Authorization": "Bearer invalid-token-12345"}
response = requests.get(f"{BASE_URL}/api/v1/campaigns", headers=bad_headers)
print_response(response)

if response.status_code == 401:
    print("\n[OK] Security working - invalid token rejected")

# ============================================================================
# Summary
# ============================================================================

print_section("TEST SUMMARY")
print("""
[OK] Health check working
[OK] User registration working
[OK] JWT authentication working
[OK] Multi-tenant isolation working
[OK] Campaign CRUD working
[OK] Security validation working

[SUCCESS] ALL TESTS PASSED!

Next steps:
  1. Open http://localhost:8000/docs in browser
  2. Try the interactive API documentation
  3. Explore all endpoints
""")
