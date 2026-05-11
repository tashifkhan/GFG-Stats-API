from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from models.canonical import make_envelope
from services import canonical_mapper
from services.profile import get_detailed_user_data


router = APIRouter(tags=["Legacy"])


@router.get("/{username}/solved-problems", deprecated=True)
async def get_solved_problems(username: str):
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
            "problems": detailed_data["allProblems"],
        }
        return make_envelope(username, await canonical_mapper.stats_from(detailed_data), legacy=legacy)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"error": True, "message": e.detail, "status_code": e.status_code, "endpoint": "solved-problems"})
