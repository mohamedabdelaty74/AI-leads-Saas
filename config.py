import os
import json
from typing import Optional
import secrets
from cryptography.fernet import Fernet

class SecureConfig:
    """Secure configuration management"""

    def __init__(self):
        self.config_file = "secure_config.json"
        self.key_file = "config.key"
        self._cipher = None
        self._load_or_create_key()

    def _load_or_create_key(self):
        """Load or create encryption key"""
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
        self._cipher = Fernet(key)

    def encrypt_value(self, value: str) -> str:
        """Encrypt a configuration value"""
        return self._cipher.encrypt(value.encode()).decode()

    def decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a configuration value"""
        return self._cipher.decrypt(encrypted_value.encode()).decode()

    def set_config(self, key: str, value: str, encrypt: bool = True):
        """Set a configuration value"""
        config = self.load_config()
        if encrypt:
            config[key] = self.encrypt_value(value)
        else:
            config[key] = value

        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def get_config(self, key: str, decrypt: bool = True) -> Optional[str]:
        """Get a configuration value"""
        config = self.load_config()
        value = config.get(key)

        if value and decrypt:
            try:
                return self.decrypt_value(value)
            except:
                return value  # Return as-is if decryption fails
        return value

    def load_config(self) -> dict:
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {}

# Initialize secure config
secure_config = SecureConfig()

# Environment variables (for production)
def get_env_var(name: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable with fallback to encrypted config"""
    env_value = os.getenv(name)
    if env_value:
        return env_value
    return secure_config.get_config(name, decrypt=True) or default

# API Keys (use environment variables in production)
GOOGLE_API_KEY = get_env_var("GOOGLE_API_KEY")
HUGGINGFACE_TOKEN = get_env_var("HUGGINGFACE_TOKEN")
HUNTER_API_KEY = get_env_var("HUNTER_API_KEY")
SERP_API_KEY = get_env_var("SERP_API_KEY")

# Email Configuration
EMAIL_ADDRESS = get_env_var("EMAIL_ADDRESS")
EMAIL_PASSWORD = get_env_var("EMAIL_PASSWORD")

# Database Configuration
DB_ENCRYPTION_KEY = get_env_var("DB_ENCRYPTION_KEY", Fernet.generate_key().decode())

# Security Settings
SECRET_KEY = get_env_var("SECRET_KEY", secrets.token_hex(32))
SESSION_TIMEOUT = 3600  # 1 hour
MAX_LOGIN_ATTEMPTS = 3
RATE_LIMIT_PER_MINUTE = 60