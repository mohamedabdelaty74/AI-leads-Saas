"""
Rate Limiting Middleware
Protects API endpoints from abuse
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
from collections import defaultdict
from typing import Dict, Tuple
import os
import logging

logger = logging.getLogger(__name__)

# Rate limit configuration from environment
RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', '100'))
RATE_LIMIT_PER_HOUR = int(os.getenv('RATE_LIMIT_PER_HOUR', '1000'))


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using in-memory storage

    For production, consider using Redis for distributed rate limiting
    """

    def __init__(self, app):
        super().__init__(app)
        # Store: {ip_address: {minute: [(timestamp, count)], hour: [(timestamp, count)]}}
        self.requests: Dict[str, Dict[str, list]] = defaultdict(lambda: {'minute': [], 'hour': []})
        self.cleanup_interval = 300  # Cleanup old entries every 5 minutes
        self.last_cleanup = time.time()

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting if disabled
        if not RATE_LIMIT_ENABLED:
            return await call_next(request)

        # Skip rate limiting for health check and docs
        if request.url.path in ['/health', '/docs', '/redoc', '/openapi.json']:
            return await call_next(request)

        # Get client IP
        client_ip = self._get_client_ip(request)

        # Check rate limits
        if not self._check_rate_limit(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": 60  # seconds
                }
            )

        # Record the request
        self._record_request(client_ip)

        # Periodic cleanup
        if time.time() - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_requests()
            self.last_cleanup = time.time()

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining_minute = self._get_remaining_requests(client_ip, 'minute')
        remaining_hour = self._get_remaining_requests(client_ip, 'hour')

        response.headers['X-RateLimit-Limit-Minute'] = str(RATE_LIMIT_PER_MINUTE)
        response.headers['X-RateLimit-Remaining-Minute'] = str(remaining_minute)
        response.headers['X-RateLimit-Limit-Hour'] = str(RATE_LIMIT_PER_HOUR)
        response.headers['X-RateLimit-Remaining-Hour'] = str(remaining_hour)

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded header (when behind proxy/load balancer)
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()

        # Check for real IP header
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip

        # Fallback to direct client
        return request.client.host if request.client else 'unknown'

    def _check_rate_limit(self, ip: str) -> bool:
        """Check if request is within rate limits"""
        current_time = time.time()

        # Check minute limit
        minute_requests = self._count_requests(ip, current_time, 60)
        if minute_requests >= RATE_LIMIT_PER_MINUTE:
            return False

        # Check hour limit
        hour_requests = self._count_requests(ip, current_time, 3600)
        if hour_requests >= RATE_LIMIT_PER_HOUR:
            return False

        return True

    def _count_requests(self, ip: str, current_time: float, window_seconds: int) -> int:
        """Count requests within time window"""
        cutoff_time = current_time - window_seconds

        window_type = 'minute' if window_seconds == 60 else 'hour'
        requests = self.requests[ip][window_type]

        # Filter requests within window
        return sum(1 for timestamp in requests if timestamp > cutoff_time)

    def _record_request(self, ip: str):
        """Record a new request"""
        current_time = time.time()
        self.requests[ip]['minute'].append(current_time)
        self.requests[ip]['hour'].append(current_time)

    def _get_remaining_requests(self, ip: str, window_type: str) -> int:
        """Get remaining requests for a window"""
        current_time = time.time()
        window_seconds = 60 if window_type == 'minute' else 3600
        limit = RATE_LIMIT_PER_MINUTE if window_type == 'minute' else RATE_LIMIT_PER_HOUR

        used = self._count_requests(ip, current_time, window_seconds)
        return max(0, limit - used)

    def _cleanup_old_requests(self):
        """Remove old request records to prevent memory bloat"""
        current_time = time.time()
        cutoff_minute = current_time - 60
        cutoff_hour = current_time - 3600

        for ip in list(self.requests.keys()):
            # Clean minute records
            self.requests[ip]['minute'] = [
                t for t in self.requests[ip]['minute'] if t > cutoff_minute
            ]

            # Clean hour records
            self.requests[ip]['hour'] = [
                t for t in self.requests[ip]['hour'] if t > cutoff_hour
            ]

            # Remove IP if no recent requests
            if not self.requests[ip]['minute'] and not self.requests[ip]['hour']:
                del self.requests[ip]

        logger.info(f"Cleaned up rate limit records. Active IPs: {len(self.requests)}")


# Production note: For distributed systems, use Redis-based rate limiting
"""
Example with Redis:

from redis import Redis
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

# Initialize
redis = Redis(host='localhost', port=6379, db=0)
await FastAPILimiter.init(redis)

# Use in routes
@app.get("/api/endpoint", dependencies=[Depends(RateLimiter(times=10, seconds=60))])
def endpoint():
    ...
"""
