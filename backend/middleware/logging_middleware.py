"""
Request Logging Middleware
Logs all API requests with timing, status codes, and errors
"""
import time
import logging
import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_requests.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all API requests with:
    - Request method and path
    - Request duration
    - Response status code
    - Client IP
    - User agent
    - Request ID for tracing
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID for tracing
        request_id = self._generate_request_id()

        # Record start time
        start_time = time.time()

        # Get client info
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")

        # Log request
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} - "
            f"IP: {client_ip} - User-Agent: {user_agent}"
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time
            duration_ms = round(duration * 1000, 2)

            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(duration_ms)

            # Log response
            logger.info(
                f"[{request_id}] {request.method} {request.url.path} - "
                f"Status: {response.status_code} - Duration: {duration_ms}ms"
            )

            # Log slow requests (> 1 second)
            if duration > 1.0:
                logger.warning(
                    f"[{request_id}] SLOW REQUEST: {request.method} {request.url.path} - "
                    f"Duration: {duration_ms}ms"
                )

            return response

        except Exception as e:
            duration = time.time() - start_time
            duration_ms = round(duration * 1000, 2)

            # Log error
            logger.error(
                f"[{request_id}] ERROR: {request.method} {request.url.path} - "
                f"Error: {str(e)} - Duration: {duration_ms}ms",
                exc_info=True
            )

            raise

    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        import uuid
        return str(uuid.uuid4())[:8]

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded IP first (behind proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to direct client
        if request.client:
            return request.client.host

        return "unknown"


class StructuredLogger:
    """
    Structured logging utility for consistent log formatting
    """

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def log_request(self, method: str, path: str, status: int, duration: float, **kwargs):
        """Log API request with structured data"""
        log_data = {
            "type": "api_request",
            "method": method,
            "path": path,
            "status": status,
            "duration_ms": round(duration * 1000, 2),
            **kwargs
        }
        self.logger.info(json.dumps(log_data))

    def log_error(self, message: str, error: Exception, **kwargs):
        """Log error with structured data"""
        log_data = {
            "type": "error",
            "message": message,
            "error": str(error),
            "error_type": type(error).__name__,
            **kwargs
        }
        self.logger.error(json.dumps(log_data), exc_info=True)

    def log_business_event(self, event: str, **kwargs):
        """Log business event (e.g., user registration, campaign creation)"""
        log_data = {
            "type": "business_event",
            "event": event,
            **kwargs
        }
        self.logger.info(json.dumps(log_data))


# Example usage
if __name__ == "__main__":
    logger = StructuredLogger("test")
    logger.log_request("GET", "/api/v1/campaigns", 200, 0.123, user_id="123")
    logger.log_business_event("user_registered", user_id="123", email="test@example.com")
