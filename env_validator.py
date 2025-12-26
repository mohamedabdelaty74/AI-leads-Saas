"""
Environment Variable Validator
Validates required environment variables on startup
"""

import os
import sys
from typing import List, Tuple
from pathlib import Path

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[INFO] Loaded environment from: {env_path}")
    else:
        print(f"[WARNING] .env file not found at: {env_path}")
except ImportError:
    print("[WARNING] python-dotenv not installed. Environment variables must be set manually.")
except Exception as e:
    print(f"[WARNING] Could not load .env file: {e}")


class EnvValidator:
    """Validates required environment variables"""

    # Required variables that MUST be set
    REQUIRED_VARS = [
        "JWT_SECRET",
    ]

    # Optional but recommended variables
    RECOMMENDED_VARS = [
        "DATABASE_URL",
        "ALLOWED_ORIGINS",
        "GOOGLE_API_KEY",
        "HUGGINGFACE_API_KEY",
    ]

    @classmethod
    def validate_required(cls) -> Tuple[bool, List[str]]:
        """
        Validate that all required environment variables are set

        Returns:
            Tuple of (all_valid: bool, missing_vars: List[str])
        """
        missing = []

        for var in cls.REQUIRED_VARS:
            value = os.getenv(var)
            if not value or value.strip() == "":
                missing.append(var)

        return len(missing) == 0, missing

    @classmethod
    def validate_recommended(cls) -> Tuple[bool, List[str]]:
        """
        Check recommended environment variables

        Returns:
            Tuple of (all_set: bool, missing_vars: List[str])
        """
        missing = []

        for var in cls.RECOMMENDED_VARS:
            value = os.getenv(var)
            if not value or value.strip() == "":
                missing.append(var)

        return len(missing) == 0, missing

    @classmethod
    def validate_and_exit_on_error(cls):
        """
        Validate environment and exit if required variables are missing
        Call this at application startup
        """
        print("=" * 60)
        print("Environment Variable Validation")
        print("=" * 60)

        # Check required variables
        all_valid, missing_required = cls.validate_required()

        if not all_valid:
            print("\n[CRITICAL] Missing required environment variables:")
            for var in missing_required:
                print(f"   - {var}")
            print("\nPlease set these in your .env file or environment.")
            print("See .env.example for reference.")
            print("\nGenerate JWT_SECRET with:")
            print('   python -c "import secrets; print(secrets.token_urlsafe(64))"')
            print("=" * 60)
            sys.exit(1)

        print("[OK] All required environment variables are set")

        # Check recommended variables
        all_recommended, missing_recommended = cls.validate_recommended()

        if not all_recommended:
            print("\n[WARNING] Missing recommended environment variables:")
            for var in missing_recommended:
                print(f"   - {var}")
            print("\nSome features may not work without these variables.")
            print("See .env.example for reference.")
        else:
            print("[OK] All recommended environment variables are set")

        print("=" * 60)
        print()


def validate_jwt_secret():
    """
    Validate JWT secret meets minimum security requirements
    """
    jwt_secret = os.getenv("JWT_SECRET") or os.getenv("JWT_SECRET_KEY")

    if not jwt_secret:
        return False, "JWT_SECRET is not set"

    # Check minimum length (64 chars recommended for HS256)
    if len(jwt_secret) < 32:
        return False, f"JWT_SECRET is too short ({len(jwt_secret)} chars). Minimum: 32 chars, Recommended: 64+ chars"

    # Expanded list of dangerous default values
    dangerous_defaults = [
        "your-secret-key-change-in-production",
        "your-jwt-secret-key-here-generate-with-secrets-token-urlsafe",
        "change-me",
        "secret",
        "your-secret-here",
        "jwt-secret",
        "your_jwt_secret",
    ]

    if jwt_secret.lower() in [d.lower() for d in dangerous_defaults]:
        return False, "JWT_SECRET is using an insecure default value! Generate a secure random value"

    return True, "JWT_SECRET is valid"


def validate_database_url():
    """
    Validate database URL format
    """
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        return True, "Using default SQLite database"

    valid_prefixes = ["sqlite://", "postgresql://", "mysql://"]

    if not any(db_url.startswith(prefix) for prefix in valid_prefixes):
        return False, f"DATABASE_URL has invalid format. Must start with: {', '.join(valid_prefixes)}"

    return True, "DATABASE_URL format is valid"


def validate_admin_password():
    """
    Validate admin password is not using defaults
    """
    admin_password = os.getenv("ADMIN_PASSWORD", "")
    environment = os.getenv("ENVIRONMENT", "development")

    dangerous_defaults = [
        "change-this-to-a-secure-password",
        "change-this-secure-password-immediately",
        "admin",
        "password",
        "admin123",
        "password123",
    ]

    if environment == "production" and admin_password.lower() in [d.lower() for d in dangerous_defaults]:
        return False, "ADMIN_PASSWORD is using a default/insecure value in PRODUCTION!"

    return True, "ADMIN_PASSWORD is acceptable"


def validate_encryption_key():
    """
    Validate encryption key format
    """
    encryption_key = os.getenv("ENCRYPTION_KEY", "")

    if not encryption_key:
        return True, "ENCRYPTION_KEY not set (optional)"

    # Should be 64 hex characters (32 bytes)
    if len(encryption_key) != 64:
        return False, f"ENCRYPTION_KEY should be 64 hex characters, got {len(encryption_key)}"

    # Check if it's a valid hex string
    try:
        int(encryption_key, 16)
    except ValueError:
        return False, "ENCRYPTION_KEY must be hexadecimal characters only"

    # Check for default value
    if encryption_key.lower() == "your-encryption-key-here-64-chars":
        return False, "ENCRYPTION_KEY is using default value! Generate with: python -c \"import secrets; print(secrets.token_hex(32))\""

    return True, "ENCRYPTION_KEY is valid"


def validate_production_config():
    """
    Additional validations for production environment
    """
    environment = os.getenv("ENVIRONMENT", "development")

    if environment != "production":
        return True, "Not in production mode"

    errors = []

    # Check if using SQLite in production
    db_url = os.getenv("DATABASE_URL", "")
    if db_url.startswith("sqlite"):
        errors.append("Using SQLite in production is not recommended. Use PostgreSQL instead.")

    # Check if using Stripe test keys in production
    stripe_key = os.getenv("STRIPE_SECRET_KEY", "")
    if stripe_key.startswith("sk_test_"):
        errors.append("Using Stripe TEST keys in production environment!")

    # Check if SendGrid is configured
    sendgrid_key = os.getenv("SENDGRID_API_KEY", "")
    if sendgrid_key in ["your-sendgrid-api-key", ""]:
        errors.append("SendGrid API key not configured for production")

    if errors:
        return False, "; ".join(errors)

    return True, "Production configuration is valid"


def run_all_validations():
    """
    Run all validation checks
    """
    # Check required environment variables
    EnvValidator.validate_and_exit_on_error()

    errors = []
    warnings = []

    # Additional security validations
    jwt_valid, jwt_msg = validate_jwt_secret()
    if not jwt_valid:
        errors.append(f"JWT Secret: {jwt_msg}")

    db_valid, db_msg = validate_database_url()
    if not db_valid:
        errors.append(f"Database URL: {db_msg}")

    admin_valid, admin_msg = validate_admin_password()
    if not admin_valid:
        errors.append(f"Admin Password: {admin_msg}")
    elif "default" in admin_msg.lower():
        warnings.append(f"Admin Password: {admin_msg}")

    enc_valid, enc_msg = validate_encryption_key()
    if not enc_valid:
        errors.append(f"Encryption Key: {enc_msg}")

    prod_valid, prod_msg = validate_production_config()
    if not prod_valid:
        errors.append(f"Production Config: {prod_msg}")

    # Print results
    if errors:
        print("\n" + "="*60)
        print("[ERROR] Security Validation Failed:")
        print("="*60)
        for error in errors:
            print(f"  ❌ {error}")
        print("="*60)
        print("\nFix these issues before starting the application.")
        print("See .env.example for reference.\n")
        sys.exit(1)

    if warnings:
        print("\n" + "="*60)
        print("[WARNING] Security Warnings:")
        print("="*60)
        for warning in warnings:
            print(f"  ⚠️  {warning}")
        print("="*60 + "\n")

    print("[OK] All validations passed!\n")


if __name__ == "__main__":
    run_all_validations()
