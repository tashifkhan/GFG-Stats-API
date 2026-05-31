from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from services.gfg_service import get_detailed_user_data, get_user_heatmap
from services import unified_mapper
from models.responses import UserProfile, SolvedProblems, UserHeatmap
from models.unified import make_envelope
from typing import Dict, Any, List, Optional

# Add a prefix to avoid route conflicts
router = APIRouter(
    prefix="",  # Keep empty prefix but we'll be more specific in route definitions
    tags=["User Profile"],
)

@router.get("/{username}/profile",
    summary="Get User's Profile Information",
    responses={
        200: {"description": "Successful response with user profile data"},
        404: {"description": "User not found"},
        422: {"description": "Unable to extract user data"},
        503: {"description": "GeeksForGeeks service unavailable"},
        504: {"description": "Request timeout"}
    })
async def get_user_profile(username: str):
    """
    Get detailed profile information for a user.
    Example: /username/profile
    """
    try:
        detailed_data = await get_detailed_user_data(username)

        # Ensure fullName is a string, not None
        if detailed_data["info"]["fullName"] is None:
            detailed_data["info"]["fullName"] = ""

        # Make sure all string fields are actual strings, not None
        for key in ["userName", "fullName", "profilePicture", "institute", "instituteRank", "currentStreak", "maxStreak"]:
            if key in detailed_data["info"] and detailed_data["info"][key] is None:
                detailed_data["info"][key] = ""

        data = unified_mapper.profile_from(detailed_data, username)
        return make_envelope(username, data, legacy=detailed_data["info"])
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": True,
                "message": e.detail,
                "status_code": e.status_code,
                "endpoint": "profile"
            }
        )

@router.get("/{username}/solved-problems",
    tags=["Problem Analysis"],
    summary="Get User's Solved Problems",
    deprecated=True,
    responses={
        200: {"description": "List of all problems solved by the user"},
        404: {"description": "User not found"},
        422: {"description": "Unable to extract user data"},
        503: {"description": "GeeksForGeeks service unavailable"},
        504: {"description": "Request timeout"}
    })
async def get_solved_problems(username: str):
    """
    Get a list of all problems solved by the user with details.
    Legacy alias; prefer ``GET /{username}/stats``.
    Example: /username/solved-problems
    """
    try:
        detailed_data = await get_detailed_user_data(username)

        difficulty_counts = {
            difficulty: stats["count"]
            for difficulty, stats in detailed_data["solvedStats"].items()
        }

        legacy = {
            "userName": username,
            "totalProblemsSolved": len(detailed_data["allProblems"]),
            "problemsByDifficulty": difficulty_counts,
            "problems": detailed_data["allProblems"]
        }
        return make_envelope(username, unified_mapper.stats_from(detailed_data), legacy=legacy)
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": True,
                "message": e.detail,
                "status_code": e.status_code,
                "endpoint": "solved-problems"
            }
        )


@router.get("/{username}/heatmap",
    tags=["Problem Analysis"],
    summary="Get User Submission Heatmap",
    responses={
        200: {"description": "Daily solved-problem heatmap for the user"},
        404: {"description": "User not found"},
        422: {"description": "Invalid heatmap filter or unable to extract user data"},
        503: {"description": "GeeksForGeeks service unavailable"},
        504: {"description": "Request timeout"}
    })
async def get_submission_heatmap(
    username: str,
    range: str = Query(default="all", pattern="^(all|last365days|year)$"),
    year: int | None = Query(default=None, ge=2000, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
):
    """
    Get daily solved-problem counts grouped by submission date.
    Example: /username/heatmap?range=last365days or /username/heatmap?range=year&year=2024
    """
    try:
        legacy = await get_user_heatmap(username, range_name=range, year=year, month=month)
        return make_envelope(username, unified_mapper.heatmap_from(legacy), legacy=legacy)
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": True,
                "message": e.detail,
                "status_code": e.status_code,
                "endpoint": "heatmap"
            }
        )
