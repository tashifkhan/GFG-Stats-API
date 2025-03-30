from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from services.gfg_service import get_detailed_user_data, get_user_stats
from models.responses import UserStats

router = APIRouter(
    tags=["User Stats"],
    responses={
        200: {"description": "User statistics summary"},
        404: {"description": "User not found"},
        503: {"description": "GeeksForGeeks service unavailable"},
        504: {"description": "Request timeout"}
    }
)

@router.get("/{username}", 
    summary="Get GeeksForGeeks User Stats", 
    response_model=UserStats)
async def get_stats_by_path(username: str):
    """
    Get user stats using username directly in the path.
    Example: /khantashif
    """
    try:
        try:
            detailed_data = await get_detailed_user_data(username)
            
            difficulty_counts = {
                difficulty.capitalize(): stats["count"] 
                for difficulty, stats in detailed_data["solvedStats"].items()
            }
            
            total_problems = detailed_data["info"]["totalProblemsSolved"]
            
            standard_difficulties = ["School", "Basic", "Easy", "Medium", "Hard"]
            for diff in standard_difficulties:
                if diff not in difficulty_counts:
                    difficulty_counts[diff] = 0
            
            result = {
                "userName": username,
                "totalProblemsSolved": total_problems
            }
            
            for key, value in difficulty_counts.items():
                result[key] = value
                
            return result
            
        except HTTPException as detailed_error:
            if detailed_error.status_code != 404:
                print(f"Detailed data fetch failed: {detailed_error.detail}. Trying fallback method...")
            
            stats = await get_user_stats(username)
            return stats
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": True,
                "message": e.detail,
                "status_code": e.status_code,
                "endpoint": "stats"
            }
        )
