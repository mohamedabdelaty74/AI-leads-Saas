"""
Security Validation Script
Validates environment variables and security configuration on startup
Prevents running with insecure default values
"""
import os
import sys
from typing import List, Tuple

# Dangerous default values that should never be used in production
DANGEROUS_DEFAULTS = {
    'JWT_SECRET': [
        'your-jwt-secret-key-here-generate-with-secrets-token-urlsafe',
        'change-me',
        'secret',
        'your-secret-here',
    ],
    'ENCRYPTION_KEY': [
        'your-encryption-key-here-64-chars',
        'change-me',
    ],
    'ADMIN_PASSWORD': [
        'change-this-to-a-secure-password',
        'change-this-secure-password-immediately',
        'admin',
        'password',
        'admin123',
    ],
    'DATABASE_URL': [
        'sqlite:///./database/elite_creatif_production.db',  # SQLite should not be used in production
    ],
}

# Required environment variables
REQUIRED_VARS = [
    'JWT_SECRET',
    'DATABASE_URL',
    'ENCRYPTION_KEY',
]

class SecurityValidationError(Exception):
    """Raised when security validation fails"""
    pass


def validate_environment() -> Tuple[bool, List[str]]:
    """
    Validate environment variables for security issues

    Returns:
        Tuple of (is_valid, list of errors)
    """
    errors = []
    environment = os.getenv('ENVIRONMENT', 'development')

    # Check for missing required variables
    for var in REQUIRED_VARS:
        value = os.getenv(var)
        if not value:
            errors.append(f"❌ Missing required environment variable: {var}")

    # Check for dangerous default values (only in production)
    if environment == 'production':
        for var, dangerous_values in DANGEROUS_DEFAULTS.items():
            value = os.getenv(var, '').lower()
            if value in [v.lower() for v in dangerous_values]:
                errors.append(
                    f"❌ CRITICAL: {var} is set to a default/insecure value! "
                    f"Generate a secure value before deploying to production."
                )

    # Validate JWT_SECRET strength
    jwt_secret = os.getenv('JWT_SECRET', '')
    if jwt_secret and len(jwt_secret) < 32:
        errors.append(
            f"⚠️  WARNING: JWT_SECRET is too short ({len(jwt_secret)} chars). "
            f"Recommended: at least 64 characters for security."
        )

    # Validate encryption key format
    encryption_key = os.getenv('ENCRYPTION_KEY', '')
    if encryption_key and len(encryption_key) != 64:
        errors.append(
            f"⚠️  WARNING: ENCRYPTION_KEY should be exactly 64 hexadecimal characters. "
            f"Current length: {len(encryption_key)}"
        )

    # Check if using SQLite in production
    if environment == 'production':
        database_url = os.getenv('DATABASE_URL', '')
        if database_url.startswith('sqlite'):
            errors.append(
                "❌ CRITICAL: Using SQLite in production is not recommended. "
                "Please use PostgreSQL for production deployments."
            )

    # Check for default Stripe test keys in production
    if environment == 'production':
        stripe_key = os.getenv('STRIPE_SECRET_KEY', '')
        if stripe_key.startswith('sk_test_'):
            errors.append(
                "⚠️  WARNING: Using Stripe TEST key in production environment. "
                "Make sure this is intentional."
            )

    return len(errors) == 0, errors


def validate_or_exit():
    """
    Run validation and exit if critical errors found
    """
    is_valid, errors = validate_environment()
    environment = os.getenv('ENVIRONMENT', 'development')

    if not is_valid:
        print("\n" + "="*70)
        print("🔒 SECURITY VALIDATION FAILED")
        print("="*70)
        print(f"\nEnvironment: {environment.upper()}\n")

        for error in errors:
            print(error)

        print("\n" + "="*70)

        # In production, exit immediately
        if environment == 'production':
            print("\n❌ Cannot start application with security issues in production.")
            print("Please fix the issues above and restart.\n")
            sys.exit(1)
        else:
            print("\n⚠️  Development mode: Continuing with warnings...")
            print("⚠️  DO NOT deploy to production without fixing these issues!\n")
    else:
        if environment == 'production':
            print("✅ Security validation passed (Production)")
        else:
            print("✅ Security validation passed (Development)")


def generate_secure_secrets():
    """
    Helper function to generate secure secrets
    Prints commands to generate secure values
    """
    print("\n" + "="*70)
    print("🔐 Generate Secure Secrets")
    print("="*70 + "\n")

    print("Run these commands to generate secure values:\n")

    print("# JWT Secret (64 characters):")
    print("python -c \"import secrets; print(secrets.token_urlsafe(64))\"\n")

    print("# Encryption Key (64 hex characters):")
    print("python -c \"import secrets; print(secrets.token_hex(32))\"\n")

    print("# Stripe Webhook Secret:")
    print("# Get from Stripe Dashboard -> Developers -> Webhooks\n")

    print("# Secure Random Password:")
    print("python -c \"import secrets, string; chars = string.ascii_letters + string.digits + '!@#$%^&*'; print(''.join(secrets.choice(chars) for _ in range(20)))\"\n")

    print("="*70 + "\n")


if __name__ == "__main__":
    # If run directly, show how to generate secrets
    import argparse

    parser = argparse.ArgumentParser(description='Validate security configuration')
    parser.add_argument('--generate', action='store_true',
                       help='Show how to generate secure secrets')
    parser.add_argument('--validate', action='store_true',
                       help='Validate current environment')

    args = parser.parse_args()

    if args.generate:
        generate_secure_secrets()
    elif args.validate:
        validate_or_exit()
    else:
        # Default: validate
        validate_or_exit()
