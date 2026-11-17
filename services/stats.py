from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import HTTPException

from services.client import PROFILE_URL, SUBMISSIONS_URL, _request_json, gather_required

STANDARD_DIFFICULTIES = ["school", "basic", "easy", "medium", "hard"]


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

    profile_data, submission_payload = await gather_required(
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
