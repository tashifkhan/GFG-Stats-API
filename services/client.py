from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import httpx
from fastapi import HTTPException

from config import settings

API_URL = "https://geeks-for-geeks-api.vercel.app/{username}"
PROFILE_URL = "https://authapi.geeksforgeeks.org/api-get/user-profile-info/"
SUBMISSIONS_URL = "https://practiceapi.geeksforgeeks.org/api/v1/user/problems/submissions/"
HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.geeksforgeeks.org",
    "Referer": "https://www.geeksforgeeks.org/",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
}

async def _request_json(method: str, url: str, **kwargs: Any) -> Dict[str, Any]:
    headers = {"User-Agent": settings.user_agent, "Accept": "application/json"}

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.request(
                method,
                url,
                headers=headers,
                timeout=settings.request_timeout,
                **kwargs,
            )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Request to GeeksForGeeks timed out. Please try again later.",
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail=(
                "Failed to connect to GeeksForGeeks. The service might be down "
                "or your internet connection is unstable."
            ),
        )

    try:
        payload = response.json()
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="Failed to parse GeeksForGeeks response.",
        )

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
            status_code=response.status_code,
            detail=f"GeeksForGeeks API error: {detail}",
        )

    return payload
