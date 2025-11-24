import re
import os
import pandas as pd
from typing import Union, List, Dict, Any
import html
import bleach
from urllib.parse import urlparse
import mimetypes

class InputValidator:
    """Comprehensive input validation and sanitization"""

    def __init__(self):
        # Allowed file extensions
        self.allowed_file_types = {'.csv', '.xlsx', '.xls'}
        self.max_file_size = 10 * 1024 * 1024  # 10MB

        # Email regex pattern
        self.email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )

        # Phone number pattern (international format)
        self.phone_pattern = re.compile(
            r'^\+?[1-9]\d{1,14}$'
        )

        # Company name pattern (alphanumeric, spaces, common punctuation)
        self.company_name_pattern = re.compile(
            r'^[a-zA-Z0-9\s\-\.\,\&\(\)\'\"]{1,200}$'
        )

        # Allowed HTML tags for text content
        self.allowed_tags = ['p', 'br', 'strong', 'em', 'u']
        self.allowed_attributes = {}

    def validate_email(self, email: str) -> bool:
        """Validate email address format"""
        if not email or len(email) > 254:
            return False
        return bool(self.email_pattern.match(email.strip()))

    def validate_phone(self, phone: str) -> bool:
        """Validate phone number format"""
        if not phone:
            return False
        # Remove common formatting characters
        clean_phone = re.sub(r'[\s\-\(\)]', '', phone.strip())
        return bool(self.phone_pattern.match(clean_phone))

    def validate_company_name(self, name: str) -> bool:
        """Validate company name"""
        if not name or len(name.strip()) < 2:
            return False
        return bool(self.company_name_pattern.match(name.strip()))

    def sanitize_text(self, text: str, allow_html: bool = False) -> str:
        """Sanitize text input"""
        if not text:
            return ""

        text = text.strip()

        if allow_html:
            # Allow only safe HTML tags
            text = bleach.clean(text,
                              tags=self.allowed_tags,
                              attributes=self.allowed_attributes,
                              strip=True)
        else:
            # Escape HTML entities
            text = html.escape(text)

        return text

    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """Validate uploaded file"""
        result = {
            'valid': False,
            'error': None,
            'file_info': None
        }

        if not os.path.exists(file_path):
            result['error'] = "File does not exist"
            return result

        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > self.max_file_size:
            result['error'] = f"File too large. Maximum size: {self.max_file_size / (1024*1024):.1f}MB"
            return result

        # Check file extension
        _, ext = os.path.splitext(file_path.lower())
        if ext not in self.allowed_file_types:
            result['error'] = f"Invalid file type. Allowed: {', '.join(self.allowed_file_types)}"
            return result

        # Check MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        allowed_mimes = {
            'text/csv',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }

        if mime_type not in allowed_mimes:
            result['error'] = "Invalid file content type"
            return result

        # Try to read file content
        try:
            if ext == '.csv':
                df = pd.read_csv(file_path, nrows=1)  # Read only first row for validation
            else:
                df = pd.read_excel(file_path, nrows=1)

            result['file_info'] = {
                'columns': list(df.columns),
                'size': file_size,
                'extension': ext
            }
            result['valid'] = True

        except Exception as e:
            result['error'] = f"Cannot read file: {str(e)}"

        return result

    def validate_dataframe_columns(self, df: pd.DataFrame, required_columns: List[str]) -> Dict[str, Any]:
        """Validate DataFrame has required columns"""
        result = {
            'valid': False,
            'missing_columns': [],
            'error': None
        }

        if df is None or df.empty:
            result['error'] = "DataFrame is empty"
            return result

        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            result['missing_columns'] = missing_columns
            result['error'] = f"Missing required columns: {', '.join(missing_columns)}"
            return result

        result['valid'] = True
        return result

    def sanitize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Sanitize DataFrame content"""
        if df is None or df.empty:
            return df

        df_clean = df.copy()

        # Sanitize text columns
        for col in df_clean.columns:
            if df_clean[col].dtype == 'object':
                df_clean[col] = df_clean[col].astype(str).apply(
                    lambda x: self.sanitize_text(x) if pd.notna(x) and x != 'nan' else ''
                )

        return df_clean

    def validate_url(self, url: str) -> bool:
        """Validate URL format"""
        if not url:
            return False

        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key format (basic check)"""
        if not api_key:
            return False

        # Basic checks
        if len(api_key) < 10 or len(api_key) > 200:
            return False

        # Should not contain spaces or special characters that might indicate tampering
        if ' ' in api_key or '\n' in api_key or '\r' in api_key:
            return False

        return True

    def validate_search_query(self, query: str) -> str:
        """Validate and sanitize search query"""
        if not query:
            return ""

        query = query.strip()

        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '|', '`']
        for char in dangerous_chars:
            query = query.replace(char, '')

        # Limit length
        if len(query) > 500:
            query = query[:500]

        return query

    def rate_limit_check(self, user_id: str, action: str, limit: int = 60, window: int = 60) -> bool:
        """Simple rate limiting check (implement with Redis or database in production)"""
        # This is a basic implementation
        # In production, use Redis or a proper rate limiting library
        import time
        from collections import defaultdict

        if not hasattr(self, '_rate_limits'):
            self._rate_limits = defaultdict(list)

        key = f"{user_id}:{action}"
        now = time.time()

        # Clean old entries
        self._rate_limits[key] = [
            timestamp for timestamp in self._rate_limits[key]
            if now - timestamp < window
        ]

        # Check limit
        if len(self._rate_limits[key]) >= limit:
            return False

        # Add current request
        self._rate_limits[key].append(now)
        return True

# Initialize validator
input_validator = InputValidator()