"""
Redis caching layer.
Caches expensive Groq + scraping results.
Falls back to a simple in-memory dict in dev (no Redis needed locally).
"""
import os
import json
import hashlib
import time
from typing import Any, Optional
from loguru import logger

# ─── Try to import Redis ───────────────────────────────────────────────
try:
    import redis
    _redis_available = True
except ImportError:
    _redis_available = False
    logger.warning("redis not installed — using in-memory cache (dev only)")

# ─── In-memory fallback (dev) ─────────────────────────────────────────
_memory_cache: dict[str, tuple[Any, float]] = {}  # key → (value, expires_at)


class Cache:
    """
    Unified cache interface.
    Uses Redis in production, memory dict in development.
    """

    def __init__(self):
        self._redis: Optional[Any] = None
        redis_url = os.environ.get("REDIS_URL")

        if redis_url and _redis_available:
            try:
                self._redis = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_timeout=2,
                    socket_connect_timeout=2,
                    retry_on_timeout=True,
                )
                self._redis.ping()
                logger.info("Cache: Redis connected")
            except Exception as e:
                logger.warning(f"Redis unavailable ({e}) — falling back to memory")
                self._redis = None
        else:
            logger.info("Cache: in-memory mode (set REDIS_URL for production)")

    def _key(self, *parts: str) -> str:
        """Build a namespaced, hashed cache key."""
        raw = ":".join(parts)
        return f"applymind:{hashlib.md5(raw.encode()).hexdigest()}"

    def get(self, *key_parts: str) -> Optional[Any]:
        key = self._key(*key_parts)
        try:
            if self._redis:
                val = self._redis.get(key)
                return json.loads(val) if val else None
            # Memory fallback
            entry = _memory_cache.get(key)
            if entry and entry[1] > time.time():
                return entry[0]
            if entry:
                del _memory_cache[key]
        except Exception as e:
            logger.debug(f"Cache get error: {e}")
        return None

    def set(self, *key_parts: str, value: Any, ttl: int = 3600):
        """Store value with TTL in seconds."""
        key = self._key(*key_parts)
        try:
            serialised = json.dumps(value, default=str)
            if self._redis:
                self._redis.setex(key, ttl, serialised)
            else:
                _memory_cache[key] = (value, time.time() + ttl)
        except Exception as e:
            logger.debug(f"Cache set error: {e}")

    def delete(self, *key_parts: str):
        key = self._key(*key_parts)
        try:
            if self._redis:
                self._redis.delete(key)
            else:
                _memory_cache.pop(key, None)
        except Exception as e:
            logger.debug(f"Cache delete error: {e}")

    def invalidate_user(self, uid: str):
        """Clear all cached data for a specific user (e.g. after resume update)."""
        try:
            if self._redis:
                pattern = f"applymind:*{uid[:8]}*"
                keys = self._redis.keys(pattern)
                if keys:
                    self._redis.delete(*keys)
        except Exception as e:
            logger.debug(f"Cache invalidation error: {e}")


# ─── Singleton ────────────────────────────────────────────────────────
_cache_instance: Optional[Cache] = None

def get_cache() -> Cache:
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = Cache()
    return _cache_instance


# ─── TTLs (seconds) ───────────────────────────────────────────────────
TTL_MARKET_REPORT = 6 * 3600      # 6 hours
TTL_JOB_SCRAPE    = 1 * 3600      # 1 hour
TTL_MATCH_SCORE   = 24 * 3600     # 24 hours
TTL_WEEKLY_REPORT = 7 * 24 * 3600 # 7 days
TTL_ATS_REWRITE   = 12 * 3600     # 12 hours
