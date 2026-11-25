"""Per-IP and per-handle counters with exponential backoff.

Every store call is bounded, so a stalled Redis degrades to "allowed" instead of
consuming the function's lifetime.
"""

import asyncio
import os
import time
from dataclasses import dataclass

from core.cache import command, get_redis as _cache_get_redis
from core.config import cache_rate_limit_settings as settings

RATE_LIMIT_TIMEOUT = 0.5
get_redis = _cache_get_redis


def _enabled() -> bool:
    """Native Redis keeps the historical behaviour; a REST-only store must opt in."""
    return bool(
        getattr(settings, "oracle_redis_url", None)
        or os.getenv("ORACLE_REDIS_URL")
        or getattr(settings, "redis_url", None)
        or getattr(settings, "rate_limit_enabled", False)
    )


async def _bounded(awaitable, timeout: float | None = None):
    limit = RATE_LIMIT_TIMEOUT if timeout is None else timeout
    try:
        return await asyncio.wait_for(awaitable, limit)
    except Exception:
        return None


@dataclass
class RateLimitResult:
    allowed: bool
    retry_after: int = 0
    limited_by: str | None = None
    limit: int | None = None
    remaining: int | None = None
    reset_at: int | None = None


async def check_rate_limit(key: str, limit: int, window_seconds: int, label: str) -> RateLimitResult:
    if not _enabled():
        return RateLimitResult(allowed=True)

    patched_client = get_redis() if get_redis is not _cache_get_redis else None
    if get_redis is not _cache_get_redis and patched_client is None:
        return RateLimitResult(allowed=True)

    async def _call(name: str, *args):
        if patched_client is not None:
            method = getattr(patched_client, name, None)
            if method is None:
                return None
            return await _bounded(method(*args))
        return await command(name, *args)

    backoff_key = f"backoff:{key}"
    violations_key = f"violations:{key}"
    counter_key = f"rl:{key}"
    now = int(time.time())

    try:
        retry_after = await _call("ttl", backoff_key)
        if isinstance(retry_after, int) and retry_after > 0:
            return RateLimitResult(False, retry_after, label, limit, 0, now + retry_after)

        count = await _call("incr", counter_key)
        if not isinstance(count, int):
            return RateLimitResult(allowed=True)
        if count == 1:
            await _call("expire", counter_key, window_seconds)
            # A fresh window clears the old escalation. The extra DEL happens
            # once per window, not on every allowed request.
            await _call("delete", violations_key)

        ttl = await _call("ttl", counter_key)
        ttl = ttl if isinstance(ttl, int) else 0
        reset_at = now + max(ttl, 0)
        remaining = max(limit - count, 0)
        if count <= limit:
            return RateLimitResult(True, 0, label, limit, remaining, reset_at)

        violations = await _call("incr", violations_key)
        violations = violations if isinstance(violations, int) and violations > 0 else 1
        await _call("expire", violations_key, settings.rate_limit_backoff_max_seconds)
        backoff = min(
            settings.rate_limit_backoff_base_seconds * (2 ** max(violations - 1, 0)),
            settings.rate_limit_backoff_max_seconds,
        )
        await _call("setex", backoff_key, backoff, "1")
        return RateLimitResult(False, backoff, label, limit, 0, now + backoff)
    except Exception:
        # Rate limiting must never take the API down.
        return RateLimitResult(allowed=True)


async def enforce_rate_limit():
    """Kept for existing dependency imports. Middleware owns the actual checks."""
    return None
