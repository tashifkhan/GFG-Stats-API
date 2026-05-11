import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import httpx
from fastapi import HTTPException

from config import settings

API_URL = "https://geeks-for-geeks-api.vercel.app/{username}"
PROFILE_URL = "https://authapi.geeksforgeeks.org/api-get/user-profile-info/"
SUBMISSIONS_URL = "https://practiceapi.geeksforgeeks.org/api/v1/user/problems/submissions/"
STANDARD_DIFFICULTIES = ["school", "basic", "easy", "medium", "hard"]
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

async def _get_profile_data(username: str) -> Dict[str, Any]:
    payload = await _request_json(
        "GET",
        PROFILE_URL,
        params={
            "handle": username,
            "article_count": "false",
            "redirect": "true",
        },
    )

    user_info = payload.get("data")
    if not user_info:
        raise HTTPException(
            status_code=404,
            detail=f"User profile information not found for '{username}'.",
        )

    return user_info

async def _get_submission_data(username: str) -> Dict[str, Any]:
    payload = await _request_json(
        "POST",
        SUBMISSIONS_URL,
        json={"handle": username, "requestType": "", "year": "", "month": ""},
    )

    if payload.get("status") == "failed":
        raise HTTPException(
            status_code=404,
            detail=f"User '{username}' not found on GeeksForGeeks",
        )

    result = payload.get("result")
    if result is None:
        raise HTTPException(
            status_code=422,
            detail=f"Could not extract solved problem data for user '{username}'.",
        )

    return payload

def _build_solved_stats(submission_payload: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    solved_stats: Dict[str, Dict[str, Any]] = {}

    for difficulty, problems in submission_payload.get("result", {}).items():
        questions = []

        for details in problems.values():
            question_info = {
                "question": details.get("pname", ""),
                "questionUrl": f"https://www.geeksforgeeks.org/problems/{details.get('slug', '')}",
                "difficulty": difficulty,
                "slug": details.get("slug", ""),
            }
            questions.append(question_info)

        solved_stats[difficulty.lower()] = {"count": len(questions), "questions": questions}

    for difficulty in STANDARD_DIFFICULTIES:
        solved_stats.setdefault(difficulty.lower(), {"count": 0, "questions": []})

    return solved_stats

def _iter_submission_details(submission_payload: Dict[str, Any]):
    for problems in submission_payload.get("result", {}).values():
        for details in problems.values():
            yield details

def _string_or_default(value: Any, default: str = "") -> str:
    if value is None or value == "":
        return default

    return str(value)

def _parse_profile_created_date(profile_data: Dict[str, Any]) -> datetime:
    created_at = profile_data.get("created_date")
    if not created_at:
        raise HTTPException(
            status_code=422,
            detail="Could not determine the GeeksForGeeks account creation date.",
        )

    try:
        return datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="Invalid GeeksForGeeks account creation date format.",
        )

async def get_detailed_user_data(username: str) -> Dict[str, Any]:
    if username == "favicon.ico":
        raise HTTPException(
            status_code=400,
            detail="Invalid username: favicon.ico is not a valid GeeksForGeeks username",
        )

    profile_data, submission_payload = await asyncio.gather(
        _get_profile_data(username),
        _get_submission_data(username),
    )
    solved_stats = _build_solved_stats(submission_payload)

    all_problems = []
    for difficulty in STANDARD_DIFFICULTIES:
        all_problems.extend(solved_stats[difficulty.lower()]["questions"])

    general_info = {
        "userName": username,
        "fullName": profile_data.get("name", "") or "",
        "profilePicture": profile_data.get("profile_image_url", "") or "",
        "institute": profile_data.get("institute_name", "") or "",
        "instituteRank": _string_or_default(profile_data.get("institute_rank")),
        "currentStreak": _string_or_default(profile_data.get("pod_solved_current_streak"), "00"),
        "maxStreak": _string_or_default(profile_data.get("pod_solved_global_longest_streak"), "00"),
        "codingScore": int(profile_data.get("score", 0) or 0),
        "monthlyScore": int(profile_data.get("monthly_score", 0) or 0),
        "totalProblemsSolved": int(
            profile_data.get("total_problems_solved", submission_payload.get("count", 0)) or 0
        ),
    }

    return {
        "info": general_info,
        "solvedStats": solved_stats,
        "allProblems": all_problems,
    }
