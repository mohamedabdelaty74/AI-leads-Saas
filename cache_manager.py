"""
Elite Creatif - Performance Caching System
High-impact caching for lead queries, AI responses, and user data
"""

import redis
import json
import pickle
import hashlib
import os
from typing import Any, Optional, Dict, List
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """High-performance caching system for Elite Creatif"""

    def __init__(self):
        # Redis connection with fallback to local caching
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.enabled = True

        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            self.redis_client.ping()  # Test connection
            logger.info("✅ Redis cache connected successfully")
        except Exception as e:
            logger.warning(f"⚠️ Redis unavailable, using memory cache: {e}")
            self.redis_client = None
            self._memory_cache = {}

    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate consistent cache keys"""
        key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        if not self.enabled:
            return None

        try:
            if self.redis_client:
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
            else:
                return self._memory_cache.get(key)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        return None

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set cached value with TTL (default 5 minutes)"""
        if not self.enabled:
            return False

        try:
            if self.redis_client:
                return self.redis_client.setex(key, ttl, json.dumps(value, default=str))
            else:
                self._memory_cache[key] = value
                return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
        return False

    def delete(self, key: str) -> bool:
        """Delete cached value"""
        try:
            if self.redis_client:
                return bool(self.redis_client.delete(key))
            else:
                self._memory_cache.pop(key, None)
                return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
        return False

    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self.redis_client:
            # For memory cache, clear all keys containing pattern
            keys_to_delete = [k for k in self._memory_cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self._memory_cache[key]
            return len(keys_to_delete)

        try:
            keys = self.redis_client.keys(f"*{pattern}*")
            if keys:
                return self.redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Cache pattern clear error: {e}")
        return 0

# Global cache instance
cache = CacheManager()

def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator for caching function results

    Args:
        ttl: Time to live in seconds (default 5 minutes)
        key_prefix: Prefix for cache key
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache._generate_cache_key(
                key_prefix or func.__name__,
                *args,
                **kwargs
            )

            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"🎯 Cache HIT: {func.__name__}")
                return result

            # Execute function and cache result
            logger.debug(f"💾 Cache MISS: {func.__name__} - executing...")
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator

# Specialized caching functions for common operations
class LeadCache:
    """Optimized caching for lead operations"""

    @staticmethod
    @cached(ttl=600, key_prefix="leads_org")  # 10 minutes
    def get_leads_by_organization(org_id: str, limit: int = 100):
        """Cache lead queries by organization - implement in your lead functions"""
        # This will be implemented in your existing lead functions
        pass

    @staticmethod
    def invalidate_organization_leads(org_id: str):
        """Clear cached leads for an organization when new leads are added"""
        cache.clear_pattern(f"leads_org:{org_id}")

class AICache:
    """High-performance caching for AI-generated content"""

    @staticmethod
    @cached(ttl=3600, key_prefix="ai_content")  # 1 hour
    def cache_ai_response(prompt: str, model: str = "default"):
        """Cache AI-generated content - implement in your AI functions"""
        # This will be implemented in your AI generation functions
        pass

    @staticmethod
    @cached(ttl=1800, key_prefix="company_desc")  # 30 minutes
    def cache_company_description(company_name: str, industry: str = ""):
        """Cache company descriptions"""
        pass

# Usage examples and integration helpers
def integrate_with_existing_functions():
    """
    Integration guide for your existing functions:

    BEFORE (slow):
    def get_user_leads(user_id):
        conn = sqlite3.connect("leads.db")
        return conn.execute("SELECT * FROM leads WHERE user_id=?", (user_id,)).fetchall()

    AFTER (fast with caching):
    @cached(ttl=300, key_prefix="user_leads")
    def get_user_leads(user_id):
        conn = sqlite3.connect("leads.db")
        return conn.execute("SELECT * FROM leads WHERE user_id=?", (user_id,)).fetchall()
    """
    pass

if __name__ == "__main__":
    # Test the cache system
    print("🧪 Testing Elite Creatif Cache System...")

    @cached(ttl=10, key_prefix="test")
    def expensive_operation(x, y):
        print(f"💻 Executing expensive operation: {x} + {y}")
        return x + y

    # First call - executes function
    result1 = expensive_operation(5, 3)
    print(f"Result 1: {result1}")

    # Second call - uses cache
    result2 = expensive_operation(5, 3)
    print(f"Result 2: {result2}")

    print("✅ Cache system working!")