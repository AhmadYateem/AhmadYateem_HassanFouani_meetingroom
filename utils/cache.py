"""
Redis caching utilities for the Smart Meeting Room system.
"""

import json
import logging
import os
from functools import wraps
from typing import Any, Callable, Dict, Optional

import redis

DEFAULT_REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
DEFAULT_REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
DEFAULT_REDIS_DB = int(os.getenv("REDIS_DB", "0"))
DEFAULT_CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))

# Strategy-specific TTLs
USER_PROFILE_TTL = 300          # 5 minutes
ROOM_AVAILABILITY_TTL = 60      # 1 minute
ROOM_DETAILS_TTL = 600          # 10 minutes
REVIEW_STATS_TTL = 300          # 5 minutes

USER_PROFILE_PATTERN = "user:{user_id}"
ROOM_AVAILABILITY_PATTERN = "room:availability:{room_id}:{date}"
ROOM_DETAILS_PATTERN = "room:{room_id}"
REVIEW_STATS_PATTERN = "reviews:stats:{room_id}"


def _get_logger() -> logging.Logger:
    """
    Try to reuse the shared JSON logger; fallback to a basic logger if unavailable.
    """
    try:
        from utils.logger import setup_logger
        return setup_logger(__name__)
    except Exception:
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            logging.basicConfig(level=logging.INFO)
        return logger


logger = _get_logger()


class RedisCache:
    """
    Redis-backed cache with JSON serialization, pooling, and helper utilities.
    """

    def __init__(
        self,
        host: str = DEFAULT_REDIS_HOST,
        port: int = DEFAULT_REDIS_PORT,
        db: int = DEFAULT_REDIS_DB,
        default_ttl: int = DEFAULT_CACHE_TTL,
    ):
        self.default_ttl = default_ttl
        self.pool = redis.ConnectionPool(
            host=host,
            port=port,
            db=db,
            decode_responses=True,
        )
        self.client = redis.Redis(connection_pool=self.pool)

    def _serialize(self, value: Any) -> str:
        try:
            return json.dumps(value)
        except (TypeError, ValueError) as exc:
            logger.warning("Failed to serialize value for cache; coercing to string", exc_info=exc)
            return json.dumps(str(value))

    def _deserialize(self, value: Optional[str]) -> Any:
        if value is None:
            return None
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            return value

    def get(self, key: str) -> Any:
        try:
            return self._deserialize(self.client.get(key))
        except redis.RedisError as exc:
            logger.error("Redis get failed", extra={"cache_key": key}, exc_info=exc)
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        expire = ttl if ttl is not None else self.default_ttl
        try:
            self.client.setex(key, expire, self._serialize(value))
            return True
        except redis.RedisError as exc:
            logger.error("Redis set failed", extra={"cache_key": key}, exc_info=exc)
            return False

    def delete(self, key: str) -> int:
        try:
            return int(self.client.delete(key))
        except redis.RedisError as exc:
            logger.error("Redis delete failed", extra={"cache_key": key}, exc_info=exc)
            return 0

    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching the pattern using scan to avoid blocking.
        """
        deleted = 0
        try:
            for key in self.client.scan_iter(match=pattern):
                deleted += int(self.client.delete(key))
        except redis.RedisError as exc:
            logger.error("Redis pattern delete failed", extra={"pattern": pattern}, exc_info=exc)
        return deleted

    def exists(self, key: str) -> bool:
        try:
            return bool(self.client.exists(key))
        except redis.RedisError as exc:
            logger.error("Redis exists check failed", extra={"cache_key": key}, exc_info=exc)
            return False

    def flush(self) -> bool:
        try:
            self.client.flushdb()
            return True
        except redis.RedisError as exc:
            logger.error("Redis flush failed", exc_info=exc)
            return False

    def get_or_set(self, key: str, callback: Callable[[], Any], ttl: Optional[int] = None) -> Any:
        cached_value = self.get(key)
        if cached_value is not None:
            return cached_value
        result = callback()
        self.set(key, result, ttl)
        return result

    def cached(self, key_pattern: Callable[..., str] | str, ttl: Optional[int] = None):
        """
        Decorator to automatically cache function results.
        """
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                cache_key = (
                    key_pattern(*args, **kwargs)
                    if callable(key_pattern)
                    else key_pattern.format(*args, **kwargs)
                )
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    return cached_value

                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                return result
            return wrapper
        return decorator


def user_profile_key(user_id: int) -> str:
    return USER_PROFILE_PATTERN.format(user_id=user_id)


def room_availability_key(room_id: int, date: str) -> str:
    return ROOM_AVAILABILITY_PATTERN.format(room_id=room_id, date=date)


def room_details_key(room_id: int) -> str:
    return ROOM_DETAILS_PATTERN.format(room_id=room_id)


def review_stats_key(room_id: int) -> str:
    return REVIEW_STATS_PATTERN.format(room_id=room_id)


def invalidate_user_profile(user_id: int) -> int:
    return cache.delete(user_profile_key(user_id))


def invalidate_room_availability(room_id: int, date: str) -> int:
    return cache.delete(room_availability_key(room_id, date))


def invalidate_room_details(room_id: int) -> int:
    return cache.delete(room_details_key(room_id))


def invalidate_review_stats(room_id: int) -> int:
    return cache.delete(review_stats_key(room_id))


def invalidate_cache(key_or_pattern: str, use_pattern: bool = False) -> int:
    """
    Invalidate a specific key or multiple keys using a pattern.
    """
    if use_pattern:
        return cache.delete_pattern(key_or_pattern)
    return cache.delete(key_or_pattern)


cache = RedisCache()

cached = cache.cached

STRATEGY_TTLS: Dict[str, int] = {
    "user_profile": USER_PROFILE_TTL,
    "room_availability": ROOM_AVAILABILITY_TTL,
    "room_details": ROOM_DETAILS_TTL,
    "review_stats": REVIEW_STATS_TTL,
}

STRATEGY_KEY_BUILDERS: Dict[str, Callable[..., str]] = {
    "user_profile": user_profile_key,
    "room_availability": room_availability_key,
    "room_details": room_details_key,
    "review_stats": review_stats_key,
}

__all__ = [
    "RedisCache",
    "cache",
    "cached",
    "invalidate_cache",
    "invalidate_user_profile",
    "invalidate_room_availability",
    "invalidate_room_details",
    "invalidate_review_stats",
    "user_profile_key",
    "room_availability_key",
    "room_details_key",
    "review_stats_key",
    "STRATEGY_TTLS",
    "STRATEGY_KEY_BUILDERS",
]
