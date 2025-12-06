"""
Security Headers Middleware
Adds security headers to all responses for production security
"""
import os
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Security configuration from environment
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses:
    - X-Frame-Options: Prevent clickjacking
    - X-Content-Type-Options: Prevent MIME sniffing
    - X-XSS-Protection: Enable XSS filter
    - Strict-Transport-Security: Enforce HTTPS
    - Content-Security-Policy: Control resource loading
    - Referrer-Policy: Control referrer information
    - Permissions-Policy: Control browser features
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.enforce_https = ENVIRONMENT == 'production'

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check HTTPS enforcement
        if self.enforce_https and request.url.scheme != 'https':
            # Redirect to HTTPS
            https_url = request.url.replace(scheme='https')
            return Response(
                status_code=301,
                headers={'Location': str(https_url)}
            )

        # Process request
        response = await call_next(request)

        # Add security headers
        self._add_security_headers(response)

        return response

    def _add_security_headers(self, response: Response):
        """Add comprehensive security headers"""

        # Prevent clickjacking - don't allow embedding in iframes
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME sniffing - force declared content type
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Enable XSS filter (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Enforce HTTPS (only in production)
        if self.enforce_https:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Content Security Policy - restrict resource loading
        # NOTE: For Next.js compatibility, we need 'unsafe-inline' for styles only in development
        # Production should use strict CSP with nonce-based approach
        if ENVIRONMENT == 'development':
            # Development: More relaxed but still secure
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' https://cdn.jsdelivr.net",  # Removed unsafe-inline/unsafe-eval
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",  # Inline styles for Next.js
                "font-src 'self' https://fonts.gstatic.com data:",
                "img-src 'self' data: https: blob:",
                "connect-src 'self' " + " ".join(ALLOWED_ORIGINS) + " ws://localhost:* http://localhost:*",
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'",
                "object-src 'none'",  # Prevent Flash/Java/other plugins
                "upgrade-insecure-requests"  # Auto-upgrade HTTP to HTTPS
            ]
        else:
            # Production: Strict CSP - consider implementing nonce-based approach
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' https://cdn.jsdelivr.net",  # NO unsafe-inline/unsafe-eval
                "style-src 'self' https://fonts.googleapis.com",  # NO unsafe-inline in production
                "font-src 'self' https://fonts.gstatic.com data:",
                "img-src 'self' data: https: blob:",
                "connect-src 'self' " + " ".join(ALLOWED_ORIGINS),
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'",
                "object-src 'none'",
                "upgrade-insecure-requests"
            ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # Control referrer information leakage
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Control browser features and APIs
        permissions_policy = [
            "geolocation=()",
            "microphone=()",
            "camera=()",
            "payment=()",
            "usb=()",
            "magnetometer=()",
            "gyroscope=()",
            "accelerometer=()"
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions_policy)

        # Prevent browser from caching sensitive responses
        if 'Cache-Control' not in response.headers:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        # Add custom server identifier
        response.headers["X-Powered-By"] = "Elite Creatif SaaS"


# Example standalone function for adding headers to specific responses
def add_security_headers(response: Response, enforce_https: bool = False):
    """
    Utility function to add security headers to a single response
    Useful for adding headers to specific endpoints
    """
    middleware = SecurityHeadersMiddleware(None)
    middleware.enforce_https = enforce_https
    middleware._add_security_headers(response)
    return response


# Development vs Production configuration
class SecurityConfig:
    """Security configuration helper"""

    @staticmethod
    def get_csp_for_env(environment: str = None) -> str:
        """Get Content Security Policy for environment"""
        env = environment or ENVIRONMENT

        if env == 'development':
            # More relaxed CSP for development
            return (
                "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "connect-src 'self' http://localhost:* ws://localhost:*"
            )
        else:
            # Strict CSP for production
            return (
                "default-src 'self'; "
                "script-src 'self' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "connect-src 'self' " + " ".join(ALLOWED_ORIGINS)
            )

    @staticmethod
    def get_cors_config() -> dict:
        """Get CORS configuration for environment"""
        return {
            "allow_origins": ALLOWED_ORIGINS,
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            "allow_headers": ["*"],
            "expose_headers": [
                "X-Request-ID",
                "X-Process-Time",
                "X-RateLimit-Limit-Minute",
                "X-RateLimit-Remaining-Minute"
            ]
        }


if __name__ == "__main__":
    # Test security config
    config = SecurityConfig()
    print("CSP for development:")
    print(config.get_csp_for_env('development'))

    print("\nCSP for production:")
    print(config.get_csp_for_env('production'))

    print("\nCORS config:")
    print(config.get_cors_config())
