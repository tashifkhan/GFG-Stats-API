"""Source cache with request deduplication and stale fallback on failure."""

import asyncio
import hashlib
import time
import uuid

from fastapi import HTTPException

from core.cache import command, get_json, redis_enabled, set_json
from core.runtime import once

RELEASE = "if redis.call('GET',KEYS[1])==ARGV[1] then return redis.call('DEL',KEYS[1]) end return 0"


async def source(key, producer, ttl=300, stale_ttl=3600):
    """Serve a cached upstream payload; on failure, prefer stale data to an error."""
    key = "source:v1:" + hashlib.sha256(key.encode()).hexdigest()

    async def load():
        cached = await get_json(key)
        if cached and time.time() - cached.get("at", 0) < ttl:
            return cached.get("data")

        store = redis_enabled()
        owner = uuid.uuid4().hex
        locked = await command("set", key + ":lease", owner, ex=10, nx=True) if store else None
        if store and not locked:
            # Another invocation is already refreshing this key.
            if cached is not None:
                return cached.get("data")
            # Bounded coalescing: a failed cache must not become an unbounded wait.
            for _ in range(3):
                await asyncio.sleep(0.05)
                shared = await get_json(key)
                if shared is not None:
                    return shared.get("data")

        try:
            data = await producer()
        except (HTTPException, TimeoutError):
            if cached is not None:
                return cached.get("data")
            raise
        else:
            await set_json(key, {"at": time.time(), "data": data}, stale_ttl)
            return data
        finally:
            if locked:
                await command("eval", RELEASE, 1, key + ":lease", owner)

    return await once(key, load)
