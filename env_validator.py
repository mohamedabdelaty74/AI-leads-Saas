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

    if len(jwt_secret) < 32:
        return False, f"JWT_SECRET is too short ({len(jwt_secret)} chars). Minimum: 32 chars"

    if jwt_secret in ["your-secret-key-change-in-production", "change-me", "secret"]:
        return False, "JWT_SECRET is using an insecure default value"

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


def run_all_validations():
    """
    Run all validation checks
    """
    # Check required environment variables
    EnvValidator.validate_and_exit_on_error()

    # Additional security validations
    jwt_valid, jwt_msg = validate_jwt_secret()
    if not jwt_valid:
        print(f"[ERROR] JWT Secret validation failed: {jwt_msg}")
        sys.exit(1)

    db_valid, db_msg = validate_database_url()
    if not db_valid:
        print(f"[ERROR] Database URL validation failed: {db_msg}")
        sys.exit(1)

    print("[OK] All validations passed!\n")


if __name__ == "__main__":
    run_all_validations()
