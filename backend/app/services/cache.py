"""Redis caching helpers with graceful local fallback."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any

from redis import Redis
from redis.exceptions import RedisError

DEFAULT_CACHE_TTL_SECONDS = 300


@lru_cache(maxsize=1)
def get_redis_client() -> Redis | None:
    """Create a Redis client when REDIS_URL is configured."""

    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        return None

    return Redis.from_url(redis_url, decode_responses=True, socket_timeout=0.5)


def get_cache_ttl_seconds() -> int:
    """Resolve cache TTL from environment with a sensible default."""

    ttl = os.getenv("REDIS_CACHE_TTL_SECONDS")
    if ttl is None:
        return DEFAULT_CACHE_TTL_SECONDS

    try:
        parsed = int(ttl)
    except ValueError:
        return DEFAULT_CACHE_TTL_SECONDS

    return parsed if parsed > 0 else DEFAULT_CACHE_TTL_SECONDS


def get_cached_value(key: str) -> Any | None:
    """Return cached JSON payload, or None when unavailable."""

    client = get_redis_client()
    if client is None:
        return None

    try:
        payload = client.get(key)
    except RedisError:
        return None

    if payload is None:
        return None

    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return None


def set_cached_value(key: str, value: Any, *, ttl_seconds: int | None = None) -> None:
    """Store JSON payload in cache and ignore connectivity failures."""

    client = get_redis_client()
    if client is None:
        return

    ttl = ttl_seconds if ttl_seconds is not None else get_cache_ttl_seconds()

    try:
        client.setex(key, ttl, json.dumps(value))
    except RedisError:
        return
