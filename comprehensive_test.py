"""
Comprehensive Project Test Suite
Tests all major functionality of Elite Creatif project
"""

import requests
import json
import time
from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

BASE_URL = "http://localhost:8000"
TEST_USER = {
    "email": f"test_{int(time.time())}@example.com",
    "password": "TestPass123!",
    "first_name": "Test",
    "last_name": "User",
    "company_name": f"Test Company {int(time.time())}",
    "company_email": f"company_{int(time.time())}@example.com",
    "company_website": "https://testcompany.com"
}

# Test results
results = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def log_test(name, status, details=""):
    """Log test result"""
    if status == "PASS":
        results["passed"].append({"test": name, "details": details})
        print(f"[PASS] {name}")
        if details:
            print(f"       {details}")
    elif status == "FAIL":
        results["failed"].append({"test": name, "details": details})
        print(f"[FAIL] {name}")
        if details:
            print(f"       {details}")
    elif status == "WARN":
        results["warnings"].append({"test": name, "details": details})
        print(f"[WARN] {name}")
        if details:
            print(f"       {details}")

print("=" * 80)
print("COMPREHENSIVE PROJECT TEST SUITE")
print("Elite Creatif - Multi-Tenant SaaS Platform")
print("=" * 80)

# ============================================================================
# SECTION 1: Backend API Tests
# ============================================================================
print("\n" + "=" * 80)
print("SECTION 1: Backend API Tests")
print("=" * 80)

# Test 1.1: Health Check
print("\n[1.1] Testing health check endpoint...")
try:
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    if response.status_code == 200:
        data = response.json()
        if data.get("status") == "healthy":
            log_test("Health Check", "PASS", f"Version: {data.get('version')}")
        else:
            log_test("Health Check", "FAIL", "Status not healthy")
    else:
        log_test("Health Check", "FAIL", f"Status code: {response.status_code}")
except Exception as e:
    log_test("Health Check", "FAIL", str(e))

# Test 1.2: API Documentation
print("\n[1.2] Testing API documentation...")
try:
    response = requests.get(f"{BASE_URL}/docs", timeout=5)
    if response.status_code == 200 and "swagger" in response.text.lower():
        log_test("API Documentation", "PASS", "Swagger UI accessible")
    else:
        log_test("API Documentation", "FAIL", f"Status: {response.status_code}")
except Exception as e:
    log_test("API Documentation", "FAIL", str(e))

# Test 1.3: User Registration
print("\n[1.3] Testing user registration...")
try:
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json=TEST_USER,
        timeout=10
    )
    if response.status_code == 201:
        data = response.json()
        if "access_token" in data and "user" in data:
            ACCESS_TOKEN = data["access_token"]
            USER_ID = data["user"]["id"]
            TENANT_ID = data["user"]["tenant_id"]
            log_test("User Registration", "PASS", f"User ID: {USER_ID}")
        else:
            log_test("User Registration", "FAIL", "Missing token or user data")
            ACCESS_TOKEN = None
    else:
        log_test("User Registration", "FAIL", f"Status: {response.status_code}, Body: {response.text[:200]}")
        ACCESS_TOKEN = None
except Exception as e:
    log_test("User Registration", "FAIL", str(e))
    ACCESS_TOKEN = None

# Test 1.4: User Login
print("\n[1.4] Testing user login...")
if ACCESS_TOKEN:
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": TEST_USER["email"], "password": TEST_USER["password"]},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                log_test("User Login", "PASS", "Login successful")
            else:
                log_test("User Login", "FAIL", "No access token returned")
        else:
            log_test("User Login", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        log_test("User Login", "FAIL", str(e))
else:
    log_test("User Login", "WARN", "Skipped (registration failed)")

# Test 1.5: Get Current User
print("\n[1.5] Testing get current user...")
if ACCESS_TOKEN:
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/auth/me",
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("email") == TEST_USER["email"]:
                log_test("Get Current User", "PASS", f"Email: {data['email']}")
            else:
                log_test("Get Current User", "FAIL", "Email mismatch")
        else:
            log_test("Get Current User", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        log_test("Get Current User", "FAIL", str(e))
else:
    log_test("Get Current User", "WARN", "Skipped (no access token)")

# Test 1.6: Get Tenant Profile
print("\n[1.6] Testing get tenant profile...")
if ACCESS_TOKEN:
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/tenants/me",
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("name") == TEST_USER["company_name"]:
                log_test("Get Tenant Profile", "PASS", f"Company: {data['name']}")
            else:
                log_test("Get Tenant Profile", "FAIL", "Company name mismatch")
        else:
            log_test("Get Tenant Profile", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        log_test("Get Tenant Profile", "FAIL", str(e))
else:
    log_test("Get Tenant Profile", "WARN", "Skipped (no access token)")

# Test 1.7: Create Campaign
print("\n[1.7] Testing create campaign...")
CAMPAIGN_ID = None
if ACCESS_TOKEN:
    try:
        campaign_data = {
            "name": "Test Campaign",
            "description": "Automated test campaign",
            "search_query": "restaurants in Dubai",
            "lead_source": "google_maps",
            "max_leads": 10,
            "description_style": "professional"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/campaigns",
            json=campaign_data,
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
            timeout=10
        )
        if response.status_code == 201:
            data = response.json()
            CAMPAIGN_ID = data.get("id")
            log_test("Create Campaign", "PASS", f"Campaign ID: {CAMPAIGN_ID}")
        else:
            log_test("Create Campaign", "FAIL", f"Status: {response.status_code}, Body: {response.text[:200]}")
    except Exception as e:
        log_test("Create Campaign", "FAIL", str(e))
else:
    log_test("Create Campaign", "WARN", "Skipped (no access token)")

# Test 1.8: List Campaigns
print("\n[1.8] Testing list campaigns...")
if ACCESS_TOKEN:
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/campaigns",
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                log_test("List Campaigns", "PASS", f"Found {len(data)} campaigns")
            else:
                log_test("List Campaigns", "FAIL", "Response not a list")
        else:
            log_test("List Campaigns", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        log_test("List Campaigns", "FAIL", str(e))
else:
    log_test("List Campaigns", "WARN", "Skipped (no access token)")

# Test 1.9: Get Campaign by ID
print("\n[1.9] Testing get campaign by ID...")
if ACCESS_TOKEN and CAMPAIGN_ID:
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/campaigns/{CAMPAIGN_ID}",
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("id") == CAMPAIGN_ID:
                log_test("Get Campaign by ID", "PASS", f"Retrieved campaign {CAMPAIGN_ID}")
            else:
                log_test("Get Campaign by ID", "FAIL", "ID mismatch")
        else:
            log_test("Get Campaign by ID", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        log_test("Get Campaign by ID", "FAIL", str(e))
else:
    log_test("Get Campaign by ID", "WARN", "Skipped (no campaign ID)")

# Test 1.10: Add Lead to Campaign
print("\n[1.10] Testing add lead to campaign...")
if ACCESS_TOKEN and CAMPAIGN_ID:
    try:
        lead_data = {
            "title": "Test Restaurant",
            "address": "123 Test St, Dubai",
            "phone": "+971501234567",
            "email": "test@restaurant.com",
            "lead_score": 80
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/campaigns/{CAMPAIGN_ID}/leads",
            json=lead_data,
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
            timeout=10
        )
        if response.status_code == 201:
            data = response.json()
            log_test("Add Lead to Campaign", "PASS", f"Lead ID: {data.get('id')}")
        else:
            log_test("Add Lead to Campaign", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        log_test("Add Lead to Campaign", "FAIL", str(e))
else:
    log_test("Add Lead to Campaign", "WARN", "Skipped (no campaign)")

# ============================================================================
# SECTION 2: Security Tests
# ============================================================================
print("\n" + "=" * 80)
print("SECTION 2: Security Tests")
print("=" * 80)

# Test 2.1: Unauthorized Access
print("\n[2.1] Testing unauthorized access protection...")
try:
    response = requests.get(f"{BASE_URL}/api/v1/campaigns", timeout=5)
    if response.status_code == 401 or response.status_code == 403:
        log_test("Unauthorized Access Protection", "PASS", "Properly blocked")
    else:
        log_test("Unauthorized Access Protection", "FAIL", f"Expected 401/403, got {response.status_code}")
except Exception as e:
    log_test("Unauthorized Access Protection", "FAIL", str(e))

# Test 2.2: Invalid Token
print("\n[2.2] Testing invalid token handling...")
try:
    response = requests.get(
        f"{BASE_URL}/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token_12345"},
        timeout=5
    )
    if response.status_code == 401:
        log_test("Invalid Token Handling", "PASS", "Properly rejected")
    else:
        log_test("Invalid Token Handling", "FAIL", f"Expected 401, got {response.status_code}")
except Exception as e:
    log_test("Invalid Token Handling", "FAIL", str(e))

# Test 2.3: Password Strength Validation
print("\n[2.3] Testing password strength validation...")
try:
    weak_user = TEST_USER.copy()
    weak_user["email"] = f"weak_{int(time.time())}@example.com"
    weak_user["password"] = "weak"
    weak_user["company_name"] = f"Weak Test {int(time.time())}"
    weak_user["company_email"] = f"weak_{int(time.time())}@example.com"

    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json=weak_user,
        timeout=10
    )
    if response.status_code == 422:  # Validation error
        log_test("Password Strength Validation", "PASS", "Weak password rejected")
    else:
        log_test("Password Strength Validation", "FAIL", f"Weak password accepted: {response.status_code}")
except Exception as e:
    log_test("Password Strength Validation", "FAIL", str(e))

# Test 2.4: Email Format Validation
print("\n[2.4] Testing email format validation...")
try:
    invalid_email_user = TEST_USER.copy()
    invalid_email_user["email"] = "not-an-email"
    invalid_email_user["company_name"] = f"Invalid Email Test {int(time.time())}"
    invalid_email_user["company_email"] = f"invalid_{int(time.time())}@example.com"

    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json=invalid_email_user,
        timeout=10
    )
    if response.status_code == 422:
        log_test("Email Format Validation", "PASS", "Invalid email rejected")
    else:
        log_test("Email Format Validation", "FAIL", f"Invalid email accepted: {response.status_code}")
except Exception as e:
    log_test("Email Format Validation", "FAIL", str(e))

# ============================================================================
# SECTION 3: Database Tests
# ============================================================================
print("\n" + "=" * 80)
print("SECTION 3: Database Tests")
print("=" * 80)

print("\n[3.1] Testing database connection...")
try:
    import psycopg2
    DATABASE_URL = os.getenv('DATABASE_URL')
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    log_test("Database Connection", "PASS", f"PostgreSQL connected")
except Exception as e:
    log_test("Database Connection", "FAIL", str(e))

print("\n[3.2] Testing database tables...")
try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = 'public';
    """)
    table_count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    if table_count >= 5:  # Should have at least 5 tables
        log_test("Database Tables", "PASS", f"Found {table_count} tables")
    else:
        log_test("Database Tables", "FAIL", f"Only {table_count} tables found")
except Exception as e:
    log_test("Database Tables", "FAIL", str(e))

# ============================================================================
# SECTION 4: Environment & Configuration
# ============================================================================
print("\n" + "=" * 80)
print("SECTION 4: Environment & Configuration Tests")
print("=" * 80)

print("\n[4.1] Testing environment variables...")
required_vars = ["JWT_SECRET", "DATABASE_URL"]
missing_vars = []
for var in required_vars:
    if not os.getenv(var):
        missing_vars.append(var)

if not missing_vars:
    log_test("Environment Variables", "PASS", "All required vars set")
else:
    log_test("Environment Variables", "FAIL", f"Missing: {', '.join(missing_vars)}")

print("\n[4.2] Testing .gitignore exists...")
gitignore_path = Path(__file__).parent / '.gitignore'
if gitignore_path.exists():
    with open(gitignore_path) as f:
        content = f.read()
        if '.env' in content and '*.db' in content:
            log_test(".gitignore Configuration", "PASS", "Properly configured")
        else:
            log_test(".gitignore Configuration", "WARN", "Missing critical entries")
else:
    log_test(".gitignore Configuration", "FAIL", ".gitignore not found")

print("\n[4.3] Testing .env.example exists...")
env_example_path = Path(__file__).parent / '.env.example'
if env_example_path.exists():
    log_test(".env.example Template", "PASS", "Template exists")
else:
    log_test(".env.example Template", "FAIL", "Template not found")

# ============================================================================
# FINAL REPORT
# ============================================================================
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)

total_tests = len(results["passed"]) + len(results["failed"]) + len(results["warnings"])
print(f"\nTotal Tests Run: {total_tests}")
print(f"Passed: {len(results['passed'])} ({len(results['passed'])/total_tests*100:.1f}%)")
print(f"Failed: {len(results['failed'])} ({len(results['failed'])/total_tests*100:.1f}% if total_tests > 0 else 0)")
print(f"Warnings: {len(results['warnings'])} ({len(results['warnings'])/total_tests*100:.1f}%)")

if results["failed"]:
    print("\n" + "=" * 80)
    print("FAILED TESTS")
    print("=" * 80)
    for item in results["failed"]:
        print(f"\n- {item['test']}")
        if item['details']:
            print(f"  {item['details']}")

if results["warnings"]:
    print("\n" + "=" * 80)
    print("WARNINGS")
    print("=" * 80)
    for item in results["warnings"]:
        print(f"\n- {item['test']}")
        if item['details']:
            print(f"  {item['details']}")

print("\n" + "=" * 80)
if len(results["failed"]) == 0:
    print("RESULT: ALL TESTS PASSED!")
elif len(results["failed"]) <= 2:
    print("RESULT: MOSTLY PASSING (Minor issues)")
else:
    print("RESULT: ATTENTION NEEDED (Multiple failures)")
print("=" * 80)
