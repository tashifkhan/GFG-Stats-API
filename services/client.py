import asyncio
import json
from core.runtime import http_client, remaining
from core.source import source
import logging
import time
from typing import Any, Dict
from urllib.parse import urlsplit

import httpx
from fastapi import HTTPException

from config import settings

logger = logging.getLogger("gfg")

PROFILE_URL = "https://authapi.geeksforgeeks.org/api-get/user-profile-info/"
SUBMISSIONS_URL = "https://practiceapi.geeksforgeeks.org/api/v1/user/problems/submissions/"


async def gather_required(*requests):
    """Cancel sibling requests when a required dependency fails or is cancelled."""
    tasks = [asyncio.ensure_future(request) for request in requests]
    try:
        return await asyncio.gather(*tasks)
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


async def _fetch_json(method: str, url: str, **kwargs: Any) -> Dict[str, Any]:
    headers = {"User-Agent": settings.user_agent, "Accept": "application/json"}
    started = time.monotonic()
    upstream = urlsplit(url).hostname
    outcome = "cancelled"
    status = None

    async def fetch():
        async with http_client() as client:
            return await client.request(
                method, url, headers=headers, timeout=min(settings.request_timeout, remaining()), **kwargs
            )

    try:
        response = await asyncio.wait_for(fetch(), timeout=settings.request_timeout)
        status = response.status_code
        outcome = "http_error" if response.is_error else "ok"
    except (httpx.TimeoutException, asyncio.TimeoutError):
        outcome = "timeout"
        raise HTTPException(
            status_code=504,
            detail="Request to GeeksForGeeks timed out. Please try again later.",
        )
    except httpx.RequestError:
        outcome = "connection_error"
        raise HTTPException(
            status_code=503,
            detail="Failed to connect to GeeksForGeeks. Please try again later.",
        )
    finally:
        logger.log(
            logging.INFO if outcome == "ok" else logging.WARNING,
            "gfg_upstream host=%s method=%s outcome=%s status=%s elapsed_ms=%d",
            upstream, method, outcome, status, int((time.monotonic() - started) * 1000),
        )

    try:
        payload = response.json()
    except ValueError:
        logger.warning("gfg_upstream host=%s outcome=invalid_json status=%s", upstream, status)
        raise HTTPException(
            status_code=502,
            detail="Failed to parse GeeksForGeeks response.",
        )

    if not isinstance(payload, dict):
        raise HTTPException(status_code=502, detail="Invalid response from GeeksForGeeks.")

    if response.status_code in {400, 404, 406}:
        message = str(payload.get("message", "")).lower()
        if "user not found" in message or "valid user details" in message:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"User '{kwargs.get('params', {}).get('handle') or kwargs.get('json', {}).get('handle')}' "
                    "not found on GeeksForGeeks"
                ),
            )

    if response.is_error:
        detail = payload.get("message") or response.reason_phrase
        raise HTTPException(
            status_code=503 if response.status_code == 429 else 502,
            detail=f"GeeksForGeeks API error: {detail}",
        )

    return payload


async def _request_json(method, url, **kwargs):
    return await source('gfg:'+method+url+json.dumps(kwargs, sort_keys=True), lambda: _fetch_json(method, url, **kwargs))
