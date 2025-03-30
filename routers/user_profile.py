from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from services.gfg_service import get_detailed_user_data
from models.responses import UserProfile, SolvedProblems
from typing import Dict, Any, List, Optional

# Add a prefix to avoid route conflicts
router = APIRouter(
    prefix="",  # Keep empty prefix but we'll be more specific in route definitions
    tags=["User Profile"],
)

@router.get("/{username}/profile",
    summary="Get User's Profile Information",
    response_model=UserProfile,
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
                
        return detailed_data["info"]
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
    response_model=SolvedProblems,
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
    Example: /username/solved-problems
    """
    try:
        detailed_data = await get_detailed_user_data(username)
        
        difficulty_counts = {
            difficulty: stats["count"] 
            for difficulty, stats in detailed_data["solvedStats"].items()
        }
        
        return {
            "userName": username,
            "totalProblemsSolved": len(detailed_data["allProblems"]),
            "problemsByDifficulty": difficulty_counts,
            "problems": detailed_data["allProblems"]
        }
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
