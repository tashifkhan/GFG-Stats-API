from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from typing import List, Dict, Optional
from pydantic import BaseModel
import httpx
from bs4 import BeautifulSoup
import asyncio

app = FastAPI(
    title="GeeksForGeeks Analytics API",
    description="""
    An API for analyzing GeeksForGeeks user statistics, including:
    * Problem solving statistics by difficulty
    * Total problems solved
    * Submission history
    * Overall coding practice metrics
    
    Use this API to get detailed insights into GFG user activity patterns.
    """,
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ProblemStats(BaseModel):
    difficulty: str
    count: int
    percentage: float

class UserStats(BaseModel):
    userName: str
    totalProblemsSolved: int
    problemsByDifficulty: List[ProblemStats]

@app.get("/",
    tags=["General"],
    summary="API Documentation",
    description="Redirects to the API documentation page")
async def root():
    return RedirectResponse(url="/docs")

async def get_user_stats(username: str) -> Dict:
    url = f"https://auth.geeksforgeeks.org/user/{username}/practice/"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=str(e))

    soup = BeautifulSoup(response.text, 'html.parser')
    data = soup.select('.tabs.tabs-fixed-width.linksTypeProblem')

    if not data:
        raise HTTPException(
            status_code=400,
            detail="Username does not exist or has not solved any problems on GeeksForGeeks"
        )

    problem_difficulty_tags = ["School", "Basic", "Easy", "Medium", "Hard"]
    problem_counts = {}
    total_problems = 0
    
    raw_data = data[0].get_text()
    current_difficulty = 0
    
    # Parse the problem counts
    for i, char in enumerate(raw_data):
        if char == '(':
            temp_start = i + 1
            temp_end = raw_data.find(')', temp_start)
            if temp_end != -1:
                problems = int(raw_data[temp_start:temp_end])
                problem_counts[problem_difficulty_tags[current_difficulty]] = problems
                total_problems += problems
                current_difficulty += 1

    # Calculate percentages and create ProblemStats objects
    problem_stats = []
    for difficulty, count in problem_counts.items():
        percentage = (count / total_problems * 100) if total_problems > 0 else 0
        problem_stats.append(ProblemStats(
            difficulty=difficulty,
            count=count,
            percentage=round(percentage, 2)
        ))

    return {
        "userName": username,
        "totalProblemsSolved": total_problems,
        "problemsByDifficulty": problem_stats
    }

@app.get("/user/{username}/stats",
    tags=["User Analytics"],
    summary="Get User's Complete Statistics",
    description="""
    Retrieves comprehensive GeeksForGeeks statistics for a user, including:
    
    - Total problems solved
    - Problem distribution by difficulty
    - Percentage breakdown of problems
    """,
    response_model=UserStats,
    responses={
        200: {
            "description": "Successfully retrieved user statistics",
            "content": {
                "application/json": {
                    "example": {
                        "userName": "example_user",
                        "totalProblemsSolved": 150,
                        "problemsByDifficulty": [
                            {"difficulty": "Easy", "count": 50, "percentage": 33.33},
                            {"difficulty": "Medium", "count": 70, "percentage": 46.67},
                            {"difficulty": "Hard", "count": 30, "percentage": 20.00}
                        ]
                    }
                }
            }
        },
        400: {"description": "User not found or has no solved problems"},
        502: {"description": "Error fetching data from GeeksForGeeks"}
    })
async def get_user_statistics(username: str):
    return await get_user_stats(username)

@app.get("/user/{username}/problems",
    tags=["Problem Analysis"],
    summary="Get User's Problem Solving Statistics",
    description="Retrieves detailed problem-solving statistics by difficulty level",
    responses={
        200: {"description": "Successfully retrieved problem statistics"},
        400: {"description": "User not found or has no solved problems"},
        502: {"description": "Error fetching data from GeeksForGeeks"}
    })
async def get_problem_statistics(
    username: str,
    difficulty: Optional[str] = Query(
        None,
        description="Filter by difficulty (School/Basic/Easy/Medium/Hard)"
    )
):
    stats = await get_user_stats(username)
    
    if difficulty:
        filtered_stats = [
            prob for prob in stats["problemsByDifficulty"]
            if prob.difficulty.lower() == difficulty.lower()
        ]
        stats["problemsByDifficulty"] = filtered_stats
    
    return stats

@app.get("/user/{username}/progress",
    tags=["Progress Tracking"],
    summary="Get User's Progress Metrics",
    description="Retrieves user's progress metrics and percentile rankings",
    responses={
        200: {"description": "Successfully retrieved progress metrics"},
        400: {"description": "User not found or has no solved problems"},
        502: {"description": "Error fetching data from GeeksForGeeks"}
    })
async def get_progress_metrics(username: str):
    stats = await get_user_stats(username)
    
    # Calculate additional metrics
    total_problems = stats["totalProblemsSolved"]
    difficulty_weights = {
        "School": 1,
        "Basic": 2,
        "Easy": 3,
        "Medium": 4,
        "Hard": 5
    }
    
    weighted_score = sum(
        prob.count * difficulty_weights[prob.difficulty]
        for prob in stats["problemsByDifficulty"]
    )
    
    return {
        "userName": username,
        "totalProblems": total_problems,
        "weightedScore": weighted_score,
        "difficultyDistribution": stats["problemsByDifficulty"],
        "progressMetrics": {
            "weightedScorePerProblem": round(weighted_score / total_problems, 2) if total_problems > 0 else 0,
            "hardProblemPercentage": next(
                (prob.percentage for prob in stats["problemsByDifficulty"] if prob.difficulty == "Hard"),
                0
            )
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=8000)
