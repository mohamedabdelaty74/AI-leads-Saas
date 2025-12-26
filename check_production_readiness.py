"""
Production Readiness Checker
Validates your environment is ready for deployment

USAGE:
    python check_production_readiness.py
"""

import os
import sys
from pathlib import Path

def check_env_file():
    """Check if .env.production exists"""
    env_file = Path(".env.production")
    if not env_file.exists():
        print("[ERROR] .env.production file not found!")
        return False
    print("[OK] .env.production file exists")
    return True

def check_required_vars():
    """Check if critical environment variables are set"""

    # Load .env.production
    env_file = Path(".env.production")
    if not env_file.exists():
        return False

    env_vars = {}
    with open(env_file, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value.strip()

    print("\nChecking Required Variables:\n")

    required = {
        "JWT_SECRET": "Security - JWT Secret",
        "ENCRYPTION_KEY": "Security - Encryption Key",
        "ADMIN_PASSWORD": "Security - Admin Password",
        "AI_MODEL_PATH": "AI - Model Configuration",
        "ENVIRONMENT": "App - Environment Setting"
    }

    all_set = True
    for var, description in required.items():
        if var in env_vars and env_vars[var] and not env_vars[var].startswith('your-'):
            print(f"[OK] {description}: Set")
        else:
            print(f"[MISSING] {description}: MISSING or DEFAULT")
            all_set = False

    print("\nChecking Production API Keys:\n")

    api_keys = {
        "GOOGLE_API_KEY": "Google Maps API",
        "SENDGRID_API_KEY": "SendGrid Email",
        "STRIPE_PUBLIC_KEY": "Stripe Payment (Public)",
        "STRIPE_SECRET_KEY": "Stripe Payment (Secret)",
        "SERPAPI_KEY": "SerpAPI Search"
    }

    needs_update = []
    for var, description in api_keys.items():
        if var in env_vars and env_vars[var] and not env_vars[var].startswith('your-'):
            print(f"[OK] {description}: Set")
        else:
            print(f"[TODO] {description}: Needs production key")
            needs_update.append(description)

    print("\nChecking URLs and Domains:\n")

    urls = {
        "FRONTEND_URL": "Frontend Domain",
        "API_URL": "API Domain",
        "ALLOWED_ORIGINS": "Allowed Origins",
        "FROM_EMAIL": "Email Sender",
        "ADMIN_EMAIL": "Admin Email"
    }

    for var, description in urls.items():
        if var in env_vars and env_vars[var] and 'yourdomain.com' not in env_vars[var]:
            print(f"[OK] {description}: Configured")
        else:
            print(f"[TODO] {description}: Needs your domain")
            needs_update.append(description)

    return all_set, needs_update

def check_model_downloaded():
    """Check if AI model is downloaded"""
    from pathlib import Path

    cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
    model_dirs = list(cache_dir.glob("models--Qwen--Qwen2.5-1.5B-Instruct*"))

    if model_dirs:
        print("\n[OK] AI Model (Qwen2.5-1.5B) is downloaded")
        return True
    else:
        print("\n[NOTE] AI Model (Qwen2.5-1.5B) not found - will download on first start")
        return False

def check_dependencies():
    """Check if required Python packages are installed"""
    print("\nChecking Dependencies:\n")

    required_packages = [
        "fastapi",
        "uvicorn",
        "transformers",
        "torch",
        "psycopg2",
        "redis",
        "sqlalchemy"
    ]

    all_installed = True
    for package in required_packages:
        try:
            __import__(package)
            print(f"[OK] {package}")
        except ImportError:
            print(f"[MISSING] {package} - NOT INSTALLED")
            all_installed = False

    return all_installed

def check_docker():
    """Check if Docker is available (for Redis)"""
    import subprocess

    print("\nChecking Docker:\n")

    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"[OK] Docker installed: {version}")

            # Check if Docker is running
            result = subprocess.run(
                ["docker", "ps"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print("[OK] Docker is running")

                # Check for Redis container
                if "redis-ai-leads" in result.stdout:
                    print("[OK] Redis container is running")
                    return True
                else:
                    print("[TODO] Redis container not running - Start with:")
                    print("   docker run -d --name redis-ai-leads -p 6379:6379 --restart unless-stopped redis:latest")
                    return False
            else:
                print("[NOTE] Docker Desktop is not running - Please start Docker Desktop")
                return False
        else:
            print("[ERROR] Docker not found")
            return False
    except Exception as e:
        print(f"[NOTE] Docker check failed: {e}")
        return False

def main():
    """Run all checks"""
    print("=" * 70)
    print("AI Leads SaaS - Production Readiness Check")
    print("=" * 70)
    print()

    # Check .env.production exists
    if not check_env_file():
        print("\n[CRITICAL] .env.production file missing!")
        print("   Run: python check_production_readiness.py to generate it")
        sys.exit(1)

    # Check required variables
    all_set, needs_update = check_required_vars()

    # Check model
    model_ready = check_model_downloaded()

    # Check dependencies
    deps_ready = check_dependencies()

    # Check Docker/Redis
    docker_ready = check_docker()

    # Final summary
    print("\n" + "=" * 70)
    print("PRODUCTION READINESS SUMMARY")
    print("=" * 70)
    print()

    if all_set and deps_ready:
        print("[OK] CORE CONFIGURATION: Ready")
    else:
        print("[!] CORE CONFIGURATION: Needs attention")

    if model_ready:
        print("[OK] AI MODEL: Downloaded and ready")
    else:
        print("[NOTE] AI MODEL: Will download on first start (~3GB, 5-10 min)")

    if docker_ready:
        print("[OK] REDIS: Running and ready")
    else:
        print("[NOTE] REDIS: Needs setup (see PRODUCTION_READINESS_GUIDE.md)")

    if needs_update:
        print("\n[ACTION REQUIRED] BEFORE DEPLOYING - Update these in .env.production:")
        for item in needs_update:
            print(f"   - {item}")

    print("\n" + "=" * 70)
    print("NEXT STEPS:")
    print("=" * 70)
    print()

    if not docker_ready:
        print("1. Start Docker Desktop")
        print("2. Run Redis: docker run -d --name redis-ai-leads -p 6379:6379 --restart unless-stopped redis:latest")
        print("3. Update .env.production with your production API keys and domain")
    else:
        print("1. Update .env.production with your production API keys and domain")
        print("2. Choose deployment platform (Railway/Render/DigitalOcean)")
        print("3. Follow deployment guide in PRODUCTION_READINESS_GUIDE.md")

    print("\nCOST ESTIMATES:")
    print("   - Railway: $15-25/month (recommended)")
    print("   - Render: $0-25/month (free tier available)")
    print("   - With 1.5B model: Zero token costs!")
    print("   - Profit margin: 95%+ possible")
    print()

    if all_set and deps_ready and docker_ready:
        print("SUCCESS: YOU'RE READY TO DEPLOY!")
    else:
        print("INCOMPLETE: Complete the steps above before deploying")

    print()
    print("=" * 70)

if __name__ == "__main__":
    main()
