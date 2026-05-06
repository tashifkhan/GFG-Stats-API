import asyncio
from collections import Counter
from datetime import datetime, timedelta
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
    range_name: str = "all",
    year: int | None = None,
    month: int | None = None,
) -> Dict[str, Any]:
    if username == "favicon.ico":
        raise HTTPException(
            status_code=400,
            detail="Invalid username: favicon.ico is not a valid GeeksForGeeks username",
        )

    if range_name not in {"all", "last365days", "year"}:
        raise HTTPException(
            status_code=422,
            detail="Range must be one of: all, last365days, year.",
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

    profile_data, submission_payload = await asyncio.gather(
        _get_profile_data(username),
        _get_submission_data(username),
    )
    created_dt = _parse_profile_created_date(profile_data)
    created_date = created_dt.date()
    today = datetime.utcnow().date()
    available_years = list(range(today.year, created_date.year - 1, -1))

    if year is not None and year not in available_years:
        raise HTTPException(
            status_code=422,
            detail=f"Year must be between {created_date.year} and {today.year} for this user.",
        )

    if range_name == "year" and year is None:
        raise HTTPException(
            status_code=422,
            detail="Year is required when range is set to 'year'.",
        )

    if range_name == "last365days" and month is not None:
        raise HTTPException(
            status_code=422,
            detail="Month filter is not supported when range is set to 'last365days'.",
        )

    from_date = created_date
    to_date = today

    if range_name == "last365days":
        from_date = max(created_date, today - timedelta(days=364))
    elif year is not None:
        from_date = datetime(year, 1, 1).date()
        to_date = datetime(year, 12, 31).date()

        if month is not None:
            from_date = datetime(year, month, 1).date()
            if month == 12:
                to_date = datetime(year, 12, 31).date()
            else:
                to_date = (datetime(year, month + 1, 1) - timedelta(days=1)).date()

        if from_date < created_date:
            from_date = created_date

    heatmap_counts: Counter[str] = Counter()

    for details in _iter_submission_details(submission_payload):
        submitted_at = details.get("user_subtime")
        if not submitted_at:
            continue

        try:
            submitted_dt = datetime.strptime(submitted_at, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue

        submitted_date = submitted_dt.date()
        if submitted_date < from_date or submitted_date > to_date:
            continue

        heatmap_counts[submitted_date.isoformat()] += 1

    heatmap = [
        {"date": date, "count": count}
        for date, count in sorted(heatmap_counts.items())
    ]

    return {
        "userName": username,
        "range": range_name,
        "accountCreatedDate": created_date.isoformat(),
        "fromDate": from_date.isoformat(),
        "toDate": to_date.isoformat(),
        "availableYears": available_years,
        "totalActiveDays": len(heatmap),
        "totalSubmissions": sum(heatmap_counts.values()),
        "heatmap": heatmap,
    }
