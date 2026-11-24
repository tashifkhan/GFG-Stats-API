"""Request-scoped HTTP clients and per-request upstream deduplication."""

import asyncio
import time
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field

import httpx


@dataclass
class RequestState:
    deadline: float
    client: httpx.AsyncClient
    tasks: dict = field(default_factory=dict)
    meta: dict = field(default_factory=dict)


state: ContextVar[RequestState | None] = ContextVar("gfg_request_state", default=None)


def remaining(default=6.0):
    """Seconds left in the request budget, or a sane default outside a request."""
    current = state.get()
    return max(0.001, current.deadline - time.monotonic()) if current else default


@asynccontextmanager
async def http_client():
    """Reuse one connection pool per request; fall back to a short-lived client."""
    current = state.get()
    if current:
        yield current.client
        return
    async with httpx.AsyncClient(timeout=4.0, follow_redirects=True) as client:
        yield client


async def once(key, producer):
    """Run one producer per request for an identical upstream call."""
    current = state.get()
    if current is None:
        return await producer()
    if key not in current.tasks:
        current.tasks[key] = asyncio.create_task(producer())
    return await current.tasks[key]
