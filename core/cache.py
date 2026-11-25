"""Optional response cache: native Redis when configured, Upstash REST otherwise.

Every operation is bounded so a stalled or unreachable store cannot consume the
function's execution budget. Redis is optional; reads fail open to ``None``.
"""

import asyncio
import inspect
import json
import os
import time
import weakref
from base64 import b64decode, b64encode
from typing import Any

import httpx
from redis import asyncio as redis

from core.config import cache_rate_limit_settings as settings
from core.runtime import remaining

REDIS_OPERATION_TIMEOUT = 0.25
ORACLE_OPERATION_TIMEOUT = 1.5
ORACLE_COOLDOWN_SECONDS = 60.0
_ORACLE_CA_TMP_PATH = "/tmp/oracle-redis-ca.pem"
_SUPPORTS_SSL_CA_DATA = "ssl_ca_data" in inspect.signature(redis.SSLConnection.__init__).parameters


async def _bounded(awaitable, timeout: float | None = None):
    """Await a store call, treating any failure or slowness as a cache miss."""
    limit = REDIS_OPERATION_TIMEOUT if timeout is None else timeout
    try:
        return await asyncio.wait_for(awaitable, limit)
    except Exception:
        return None


class UpstashRestRedis:
    """Minimal Redis-over-HTTP client for Upstash's REST API."""

    def __init__(self, url: str, token: str):
        self._url = url.strip().rstrip("/")
        if not self._url.startswith(("https://", "http://")):
            self._url = "https://" + self._url
        self._headers = {"Authorization": "Bearer " + token}

    async def _command(self, *parts):
        async def execute():
            async with httpx.AsyncClient(timeout=REDIS_OPERATION_TIMEOUT) as client:
                response = await client.post(
                    self._url, headers=self._headers, json=[str(part) for part in parts]
                )
            if response.status_code != 200:
                return None
            body = response.json()
            return None if body.get("error") else body.get("result")

        return await _bounded(execute())

    async def get(self, key):
        return await self._command("GET", key)

    async def set(self, key, value, ex=None, nx=False):
        parts = ["SET", key, value]
        if ex is not None:
            parts += ["EX", ex]
        if nx:
            parts += ["NX"]
        return await self._command(*parts)

    async def setex(self, key, ttl, value):
        return await self._command("SET", key, value, "EX", ttl)

    async def ttl(self, key):
        value = await self._command("TTL", key)
        try:
            return int(value)
        except (TypeError, ValueError):
            return -2

    async def incr(self, key):
        value = await self._command("INCR", key)
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    async def expire(self, key, ttl):
        return await self._command("EXPIRE", key, ttl)

    async def delete(self, key):
        return await self._command("DEL", key)

    async def eval(self, script, numkeys, *args):
        return await self._command("EVAL", script, numkeys, *args)


_client = None
_native_clients = weakref.WeakKeyDictionary()


def _rest_settings():
    return (
        getattr(settings, "upstash_rest_url", None),
        getattr(settings, "upstash_rest_token", None),
    )


_oracle_clients = weakref.WeakKeyDictionary()
_oracle_cooldown_until = 0.0


def _oracle_settings():
    url = getattr(settings, "oracle_redis_url", None)
    if url is None:
        url = os.getenv("ORACLE_REDIS_URL")
    url = url.strip() or None if isinstance(url, str) else None
    ca_cert = getattr(settings, "oracle_redis_ca_cert", None)
    if ca_cert is None:
        ca_cert = os.getenv("ORACLE_REDIS_CA_CERT")
    return url, ca_cert


def _oracle_url():
    url, _ = _oracle_settings()
    return url


def _normalize_ca_pem(raw):
    if not raw or not isinstance(raw, str):
        return None
    text = raw.strip()
    if not text:
        return None
    if "-----BEGIN" not in text and os.path.isfile(text):
        with open(text, "r", encoding="utf-8") as fh:
            text = fh.read().strip()
    elif "\\n" in text and "\n" not in text:
        text = text.replace("\\n", "\n")
    return text or None


def _oracle_ssl_kwargs(url, ca_raw):
    kwargs = {}
    ca_pem = _normalize_ca_pem(ca_raw)
    if ca_pem:
        kwargs["ssl_cert_reqs"] = "required"
        if _SUPPORTS_SSL_CA_DATA:
            kwargs["ssl_ca_data"] = ca_pem
        else:
            fd = os.open(_ORACLE_CA_TMP_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(ca_pem)
                if not ca_pem.endswith("\n"):
                    fh.write("\n")
            kwargs["ssl_ca_certs"] = _ORACLE_CA_TMP_PATH
    elif url.lower().startswith("rediss://"):
        kwargs["ssl_cert_reqs"] = "required"
    return kwargs


def _oracle_in_cooldown():
    return time.monotonic() < _oracle_cooldown_until


def _trip_oracle_cooldown():
    global _oracle_cooldown_until
    _oracle_cooldown_until = time.monotonic() + ORACLE_COOLDOWN_SECONDS


def reset_oracle_state():
    global _oracle_cooldown_until
    _oracle_cooldown_until = 0.0
    _oracle_clients.clear()


def get_oracle_redis():
    url, ca_raw = _oracle_settings()
    if not url:
        return None
    loop = asyncio.get_running_loop()
    cache_key = (url, ca_raw)
    entry = _oracle_clients.get(loop)
    if entry is None or entry[0] != cache_key:
        client = redis.from_url(
            url,
            decode_responses=True,
            socket_timeout=ORACLE_OPERATION_TIMEOUT,
            socket_connect_timeout=ORACLE_OPERATION_TIMEOUT,
            **_oracle_ssl_kwargs(url, ca_raw),
        )
        _oracle_clients[loop] = (cache_key, client)
        return client
    return entry[1]


def redis_enabled() -> bool:
    url, token = _rest_settings()
    return bool(_oracle_url() or getattr(settings, "redis_url", None) or (url and token))


def get_redis():
    """One client per event loop: an AsyncClient cannot cross loops safely."""
    global _client
    if getattr(settings, "redis_url", None):
        loop = asyncio.get_running_loop()
        if loop not in _native_clients:
            _native_clients[loop] = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_timeout=REDIS_OPERATION_TIMEOUT,
                socket_connect_timeout=REDIS_OPERATION_TIMEOUT,
            )
        return _native_clients[loop]
    if _client is not None:
        return _client
    url, token = _rest_settings()
    if url and token:
        _client = UpstashRestRedis(url, token)
    return _client


async def command(name, *args, **kwargs):
    if _oracle_url() and not _oracle_in_cooldown():
        try:
            oracle_client = get_oracle_redis()
            method = getattr(oracle_client, name, None) if oracle_client is not None else None
            if method is not None:
                return await asyncio.wait_for(method(*args, **kwargs), min(ORACLE_OPERATION_TIMEOUT, remaining()))
        except Exception:
            _trip_oracle_cooldown()

    client = get_redis()
    if client is None:
        return None
    method = getattr(client, name, None)
    if method is None:
        return None
    return await _bounded(method(*args, **kwargs), min(REDIS_OPERATION_TIMEOUT, remaining()))


async def get_json(key: str) -> dict[str, Any] | None:
    value = await command("get", key)
    if value is None:
        return None
    try:
        payload = json.loads(value) if isinstance(value, (str, bytes)) else value
    except (ValueError, TypeError):
        return None
    return payload if isinstance(payload, dict) else None


async def set_json(key: str, value: dict[str, Any], ttl_seconds: int) -> None:
    await command("setex", key, ttl_seconds, json.dumps(value, separators=(",", ":")))


async def delete_key(key: str) -> None:
    await command("delete", key)


def encode_body(body: bytes) -> str:
    return b64encode(body).decode("ascii")


def decode_body(body: str) -> bytes:
    return b64decode(body.encode("ascii"))
