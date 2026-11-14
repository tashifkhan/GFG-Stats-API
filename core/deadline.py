"""Bound the complete request, including cache and optional enrichment."""

import asyncio
import logging
import time

import httpx
from starlette.responses import JSONResponse

from config import settings
from core.runtime import RequestState, state

logger = logging.getLogger("gfg")

# Per-phase ceiling for the shared client; the request budget below is the total.
CLIENT_TIMEOUT = 4.0


def route_template(scope) -> str:
    """Route template, never the concrete handle or query string."""
    route = scope.get("route")
    if route is not None:
        return getattr(route, "path", None) or "unmatched"
    template = scope.get("path") or ""
    for name, value in (scope.get("path_params") or {}).items():
        if value:
            template = template.replace(str(value), "{" + name + "}")
    return template or "unmatched"


class RequestDeadlineMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        started = time.monotonic()
        timeout = max(0.05, float(settings.response_timeout))
        response_started = False
        status = 500
        cache = "disabled"

        async def tracked_send(message):
            nonlocal response_started, status, cache
            if message["type"] == "http.response.start":
                response_started = True
                status = message["status"]
                cache = dict(message.get("headers", [])).get(b"x-cache", b"disabled").decode()
            await send(message)

        async with httpx.AsyncClient(
            timeout=min(CLIENT_TIMEOUT, timeout), follow_redirects=True
        ) as client:
            token = state.set(RequestState(deadline=started + timeout, client=client))
            try:
                await asyncio.wait_for(self.app(scope, receive, tracked_send), timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning("gfg_request outcome=deadline response_started=%s", response_started)
                if response_started:
                    # Headers are already on the wire; ASGI cannot replace them.
                    raise
                template = route_template(scope)
                endpoint = template.rstrip("/").rsplit("/", 1)[-1]
                response = JSONResponse(
                    status_code=504,
                    content={
                        "error": True,
                        "message": "Request timed out. Please try again later.",
                        "status_code": 504,
                        "endpoint": endpoint,
                    },
                    headers={"Cache-Control": "no-store"},
                )
                await response(scope, receive, tracked_send)
            finally:
                state.reset(token)
                logger.log(
                    logging.WARNING if status >= 500 else logging.INFO,
                    "gfg_request route=%s method=%s status=%d cache=%s elapsed_ms=%d",
                    route_template(scope), scope["method"], status, cache,
                    int((time.monotonic() - started) * 1000),
                )
