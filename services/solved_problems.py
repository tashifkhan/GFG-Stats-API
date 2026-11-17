from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import HTTPException

from services.client import PROFILE_URL, SUBMISSIONS_URL, _request_json

STANDARD_DIFFICULTIES = ["school", "basic", "easy", "medium", "hard"]


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
