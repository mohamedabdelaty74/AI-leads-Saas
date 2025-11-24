"""
Test Project Modules (AI, Scrapers, etc.)
"""

import sys
from pathlib import Path

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
print("MODULE TESTS")
print("Elite Creatif - Component Testing")
print("=" * 80)

# ============================================================================
# SECTION 1: Import Tests
# ============================================================================
print("\n" + "=" * 80)
print("SECTION 1: Module Import Tests")
print("=" * 80)

print("\n[1.1] Testing backend auth module...")
try:
    from backend.auth import hash_password, verify_password, create_token_pair
    password = "TestPassword123"
    hashed = hash_password(password)
    if verify_password(password, hashed):
        log_test("Auth Module Import", "PASS", "Password hashing works")
    else:
        log_test("Auth Module Import", "FAIL", "Password verification failed")
except Exception as e:
    log_test("Auth Module Import", "FAIL", str(e))

print("\n[1.2] Testing models...")
try:
    from models.user import User
    from models.tenant import Tenant
    from models.campaign import Campaign
    log_test("Models Import", "PASS", "All models importable")
except Exception as e:
    log_test("Models Import", "FAIL", str(e))

print("\n[1.3] Testing config module...")
try:
    from config import SecureConfig
    config = SecureConfig()
    log_test("Config Module", "PASS", "SecureConfig loadable")
except Exception as e:
    log_test("Config Module", "FAIL", str(e))

print("\n[1.4] Testing environment validator...")
try:
    from env_validator import EnvValidator
    all_valid, missing = EnvValidator.validate_required()
    if all_valid:
        log_test("Environment Validator", "PASS", "Validation works")
    else:
        log_test("Environment Validator", "FAIL", f"Missing vars: {missing}")
except Exception as e:
    log_test("Environment Validator", "FAIL", str(e))

# ============================================================================
# SECTION 2: Scraper Tests
# ============================================================================
print("\n" + "=" * 80)
print("SECTION 2: Scraper Module Tests")
print("=" * 80)

print("\n[2.1] Testing Google scraper import...")
try:
    from scrapers import google_scrapers_fixed
    log_test("Google Scraper Import", "PASS", "Module importable")
except Exception as e:
    log_test("Google Scraper Import", "FAIL", str(e))

print("\n[2.2] Testing contact extractor...")
try:
    from scrapers import contact_extractor
    if hasattr(contact_extractor, 'extract_emails'):
        log_test("Contact Extractor", "PASS", "Has extract_emails function")
    else:
        log_test("Contact Extractor", "WARN", "Missing extract_emails")
except Exception as e:
    log_test("Contact Extractor", "FAIL", str(e))

print("\n[2.3] Testing LinkedIn scraper...")
try:
    from scrapers import linkedin_scraper
    log_test("LinkedIn Scraper Import", "PASS", "Module importable")
except Exception as e:
    log_test("LinkedIn Scraper Import", "FAIL", str(e))

print("\n[2.4] Testing Instagram scraper...")
try:
    from scrapers import instagram_scraper
    log_test("Instagram Scraper Import", "PASS", "Module importable")
except Exception as e:
    log_test("Instagram Scraper Import", "FAIL", str(e))

# ============================================================================
# SECTION 3: AI Generation Tests
# ============================================================================
print("\n" + "=" * 80)
print("SECTION 3: AI Generation Module Tests")
print("=" * 80)

print("\n[3.1] Testing description generator import...")
try:
    from gen import generate_description
    log_test("Description Generator Import", "PASS", "Module importable")
except Exception as e:
    log_test("Description Generator Import", "FAIL", str(e))

print("\n[3.2] Testing fast description generator...")
try:
    from gen import generate_description_fast
    log_test("Fast Description Generator", "PASS", "Module importable")
except Exception as e:
    log_test("Fast Description Generator", "FAIL", str(e))

print("\n[3.3] Testing email generator...")
try:
    from gen import generate_mail
    log_test("Email Generator Import", "PASS", "Module importable")
except Exception as e:
    log_test("Email Generator Import", "FAIL", str(e))

print("\n[3.4] Testing WhatsApp generator...")
try:
    from gen import generate_whats
    log_test("WhatsApp Generator Import", "PASS", "Module importable")
except Exception as e:
    log_test("WhatsApp Generator Import", "FAIL", str(e))

# ============================================================================
# SECTION 4: File Structure Tests
# ============================================================================
print("\n" + "=" * 80)
print("SECTION 4: File Structure Tests")
print("=" * 80)

print("\n[4.1] Testing critical files exist...")
critical_files = [
    "backend/main.py",
    "backend/auth.py",
    "backend/dependencies.py",
    "backend/schemas.py",
    "models/base.py",
    "models/user.py",
    "models/tenant.py",
    "models/campaign.py",
    "requirements.txt",
    "Dockerfile",
    "docker-compose.yml",
    ".gitignore",
    ".env.example"
]

missing_files = []
for file in critical_files:
    file_path = Path(__file__).parent / file
    if not file_path.exists():
        missing_files.append(file)

if not missing_files:
    log_test("Critical Files", "PASS", f"All {len(critical_files)} files present")
else:
    log_test("Critical Files", "FAIL", f"Missing: {', '.join(missing_files)}")

print("\n[4.2] Testing database directory...")
db_dir = Path(__file__).parent / "database"
if db_dir.exists():
    log_test("Database Directory", "PASS", "Directory exists")
else:
    log_test("Database Directory", "WARN", "Directory not found (will be created)")

print("\n[4.3] Testing models directory...")
models_dir = Path(__file__).parent / "models"
if models_dir.exists():
    model_files = list(models_dir.glob("*.py"))
    log_test("Models Directory", "PASS", f"Found {len(model_files)} model files")
else:
    log_test("Models Directory", "FAIL", "Directory not found")

# ============================================================================
# SECTION 5: Dependencies Tests
# ============================================================================
print("\n" + "=" * 80)
print("SECTION 5: Python Dependencies Tests")
print("=" * 80)

print("\n[5.1] Testing critical packages...")
critical_packages = [
    ("fastapi", "FastAPI"),
    ("sqlalchemy", "SQLAlchemy"),
    ("pydantic", "Pydantic"),
    ("psycopg2", "PostgreSQL Driver"),
    ("uvicorn", "Uvicorn"),
    ("passlib", "Passlib"),
    ("python_jose", "Python-JOSE"),
    ("python_dotenv", "Python-dotenv"),
    ("requests", "Requests"),
    ("pandas", "Pandas")
]

missing_packages = []
for package, name in critical_packages:
    try:
        __import__(package)
    except ImportError:
        missing_packages.append(name)

if not missing_packages:
    log_test("Critical Packages", "PASS", f"All {len(critical_packages)} packages installed")
else:
    log_test("Critical Packages", "FAIL", f"Missing: {', '.join(missing_packages)}")

print("\n[5.2] Testing optional AI packages...")
ai_packages = [
    ("torch", "PyTorch", False),
    ("transformers", "Transformers", False),
    ("gradio", "Gradio", False)
]

for package, name, required in ai_packages:
    try:
        __import__(package)
        log_test(f"{name} Package", "PASS", "Installed")
    except ImportError:
        if required:
            log_test(f"{name} Package", "FAIL", "Not installed (required)")
        else:
            log_test(f"{name} Package", "WARN", "Not installed (optional for AI features)")

# ============================================================================
# FINAL REPORT
# ============================================================================
print("\n" + "=" * 80)
print("MODULE TEST SUMMARY")
print("=" * 80)

total_tests = len(results["passed"]) + len(results["failed"]) + len(results["warnings"])
print(f"\nTotal Tests Run: {total_tests}")
print(f"Passed: {len(results['passed'])} ({len(results['passed'])/total_tests*100:.1f}%)")
print(f"Failed: {len(results['failed'])} ({len(results['failed'])/total_tests*100:.1f}%)")
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
    print("RESULT: ALL MODULE TESTS PASSED!")
elif len(results["failed"]) <= 2:
    print("RESULT: MOSTLY PASSING (Minor issues)")
else:
    print("RESULT: ATTENTION NEEDED (Multiple failures)")
print("=" * 80)
