import asyncio
from collections import Counter
from datetime import datetime
from typing import Any, Dict

import httpx
from fastapi import HTTPException

from config import settings


PROFILE_API_URL = "https://authapi.geeksforgeeks.org/api-get/user-profile-info/"
SUBMISSIONS_API_URL = "https://practiceapi.geeksforgeeks.org/api/v1/user/problems/submissions/"
STANDARD_DIFFICULTIES = ["School", "Basic", "Easy", "Medium", "Hard"]


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
        PROFILE_API_URL,
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
        SUBMISSIONS_API_URL,
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


async def get_user_stats(username: str) -> Dict[str, Any]:
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

    values = {
        "userName": username,
        "totalProblemsSolved": int(
            profile_data.get("total_problems_solved", submission_payload.get("count", 0)) or 0
        ),
    }

    for difficulty in STANDARD_DIFFICULTIES:
        values[difficulty] = solved_stats[difficulty.lower()]["count"]

    return values


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


async def get_user_heatmap(
    username: str,
    year: int | None = None,
    month: int | None = None,
) -> Dict[str, Any]:
    if username == "favicon.ico":
        raise HTTPException(
            status_code=400,
            detail="Invalid username: favicon.ico is not a valid GeeksForGeeks username",
        )

    if month is not None and year is None:
        raise HTTPException(
            status_code=422,
            detail="Year is required when filtering heatmap data by month.",
        )

    if month is not None and not 1 <= month <= 12:
        raise HTTPException(
            status_code=422,
            detail="Month must be between 1 and 12.",
        )

    submission_payload = await _get_submission_data(username)
    heatmap_counts: Counter[str] = Counter()

    for details in _iter_submission_details(submission_payload):
        submitted_at = details.get("user_subtime")
        if not submitted_at:
            continue

        try:
            submitted_dt = datetime.strptime(submitted_at, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue

        if year is not None and submitted_dt.year != year:
            continue

        if month is not None and submitted_dt.month != month:
            continue

        heatmap_counts[submitted_dt.date().isoformat()] += 1

    heatmap = [
        {"date": date, "count": count}
        for date, count in sorted(heatmap_counts.items())
    ]

    return {
        "userName": username,
        "totalActiveDays": len(heatmap),
        "totalSubmissions": sum(heatmap_counts.values()),
        "heatmap": heatmap,
    }
