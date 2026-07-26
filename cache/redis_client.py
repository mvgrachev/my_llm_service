"""Redis cache client for LLM Service."""
import json
import hashlib
import logging
from typing import Optional, Any
from datetime import timedelta

logger = logging.getLogger('llm_service.cache')


class InMemoryCache:
    """In-memory cache for when Redis is unavailable."""
    
    def __init__(self):
        self._cache = {}
    
    def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        logger.info(f"[CACHE InMemory] Hit for key: {key[:50]}...")
        return self._cache.get(key)
    
    def set(self, key: str, value: Any, ttl: int = 600) -> bool:
        """Set value in cache with TTL (ignored for in-memory)."""
        self._cache[key] = json.dumps(value)
        logger.debug(f"[CACHE InMemory] Set key: {key[:50]}... with TTL: {ttl}s")
        return True
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"[CACHE InMemory] Deleted key: {key[:50]}...")
            return True
        return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        return key in self._cache


class CacheClient:
    """Redis cache client for storing and retrieving LLM responses."""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, url: str = None):
        """
        Initialize Redis cache client.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            url: Redis URL (overrides host/port/db)
        """
        self.redis_available = False
        self._cache = None
        
        try:
            import redis
            if url:
                self._cache = redis.from_url(url)
            else:
                self._cache = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            # Test connection
            self._cache.ping()
            self.redis_available = True
        except Exception:
            # Fall back to in-memory cache
            self._cache = InMemoryCache()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            value = self._cache.get(key)
            if value:
                logger.info(f"[CACHE Redis] Hit for key: {key[:50]}...")
                # Handle both string (Redis) and dict (InMemoryCache) types
                if isinstance(value, str):
                    return json.loads(value)
                return value
            else:
                logger.info(f"[CACHE Redis] Miss for key: {key[:50]}...")
            return None
        except Exception as e:
            logger.error(f"[CACHE Redis] Error getting key {key[:50]}...: {str(e)}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 600) -> bool:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default 600 = 10 minutes)
            
        Returns:
            True if successful
        """
        try:
            if hasattr(self._cache, 'setex') and self.redis_available:
                self._cache.setex(key, ttl, json.dumps(value))
            else:
                self._cache.set(key, value, ttl)
            logger.debug(f"[CACHE Redis] Set key: {key[:50]}... with TTL: {ttl}s")
            return True
        except Exception as e:
            logger.error(f"[CACHE Redis] Error setting key {key[:50]}...: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted
        """
        try:
            self._cache.delete(key)
            logger.debug(f"[CACHE Redis] Deleted key: {key[:50]}...")
            return True
        except Exception as e:
            logger.error(f"[CACHE Redis] Error deleting key {key[:50]}...: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists
        """
        try:
            if hasattr(self._cache, 'exists') and self.redis_available:
                return self._cache.exists(key) > 0
            return self._cache.exists(key)
        except Exception as e:
            logger.error(f"[CACHE Redis] Error checking key existence {key[:50]}...: {str(e)}")
            return False


# Default cache instance
cache = CacheClient()
