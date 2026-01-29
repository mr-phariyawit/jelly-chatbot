"""
Caching Layer
Uses Redis when available (production), falls back to in-memory TTL cache (development).
Caches bot config, query embeddings, and other frequently accessed data.
"""

import os
import json
import time
import logging
import hashlib
from typing import Optional, Any

logger = logging.getLogger(__name__)

# In-memory fallback cache with TTL
_memory_cache: dict = {}  # key -> {"value": ..., "expires_at": ...}


def _get_redis_client():
    """Get Redis client if REDIS_URL is configured."""
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        return None
    try:
        import redis
        return redis.from_url(redis_url, decode_responses=True)
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}. Using in-memory cache.")
        return None


# Singleton Redis client (None if not available)
_redis = _get_redis_client()


def _make_key(namespace: str, key: str) -> str:
    """Create a namespaced cache key."""
    return f"jelly:{namespace}:{key}"


def _hash_key(text: str) -> str:
    """Hash a long string (e.g., query text) into a short cache key."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def cache_get(namespace: str, key: str) -> Optional[Any]:
    """Get a value from cache. Returns None if not found or expired."""
    full_key = _make_key(namespace, key)

    if _redis:
        try:
            val = _redis.get(full_key)
            if val:
                return json.loads(val)
        except Exception as e:
            logger.warning(f"Redis GET error: {e}")
        return None

    # In-memory fallback
    entry = _memory_cache.get(full_key)
    if entry and entry["expires_at"] > time.time():
        return entry["value"]
    elif entry:
        del _memory_cache[full_key]
    return None


def cache_set(namespace: str, key: str, value: Any, ttl_seconds: int = 300):
    """Set a value in cache with TTL (default 5 minutes)."""
    full_key = _make_key(namespace, key)

    if _redis:
        try:
            _redis.setex(full_key, ttl_seconds, json.dumps(value, ensure_ascii=False, default=str))
            return
        except Exception as e:
            logger.warning(f"Redis SET error: {e}")

    # In-memory fallback
    _memory_cache[full_key] = {
        "value": value,
        "expires_at": time.time() + ttl_seconds,
    }

    # Evict old entries if memory cache grows too large
    if len(_memory_cache) > 1000:
        _evict_expired()


def cache_delete(namespace: str, key: str):
    """Delete a value from cache."""
    full_key = _make_key(namespace, key)

    if _redis:
        try:
            _redis.delete(full_key)
            return
        except Exception as e:
            logger.warning(f"Redis DELETE error: {e}")

    _memory_cache.pop(full_key, None)


def cache_clear_namespace(namespace: str):
    """Clear all keys in a namespace."""
    prefix = f"jelly:{namespace}:"

    if _redis:
        try:
            cursor = 0
            while True:
                cursor, keys = _redis.scan(cursor, match=f"{prefix}*", count=100)
                if keys:
                    _redis.delete(*keys)
                if cursor == 0:
                    break
            return
        except Exception as e:
            logger.warning(f"Redis CLEAR error: {e}")

    # In-memory fallback
    to_delete = [k for k in _memory_cache if k.startswith(prefix)]
    for k in to_delete:
        del _memory_cache[k]


def _evict_expired():
    """Remove expired entries from in-memory cache."""
    now = time.time()
    to_delete = [k for k, v in _memory_cache.items() if v["expires_at"] <= now]
    for k in to_delete:
        del _memory_cache[k]


# --- Convenience functions for common cache patterns ---

def get_bot_config(bot_id: str) -> Optional[dict]:
    """Get cached bot configuration."""
    return cache_get("bot_config", bot_id)


def set_bot_config(bot_id: str, config: dict, ttl: int = 600):
    """Cache bot configuration (10 min default)."""
    cache_set("bot_config", bot_id, config, ttl)


def invalidate_bot_config(bot_id: str):
    """Invalidate bot config cache (call after bot update)."""
    cache_delete("bot_config", bot_id)


def get_cached_embedding(text: str) -> Optional[list]:
    """Get cached query embedding."""
    key = _hash_key(text)
    return cache_get("embedding", key)


def set_cached_embedding(text: str, embedding: list, ttl: int = 3600):
    """Cache query embedding (1 hour default)."""
    key = _hash_key(text)
    cache_set("embedding", key, embedding, ttl)
