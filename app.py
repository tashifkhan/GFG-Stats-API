from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from typing import List, Dict, Optional
from pydantic import BaseModel
import httpx
from bs4 import BeautifulSoup
import asyncio
import re

app = FastAPI(
    title="GeeksForGeeks Analytics API",
    description="""
    An API for analyzing GeeksForGeeks user statistics, including:
    * Problem solving statistics by difficulty
    * Total problems solved
    * Submission history
    * Overall coding practice metrics
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

async def get_user_stats(username: str) -> Dict:
    url = f"https://www.geeksforgeeks.org/user/{username}/"
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = await client.get(url, headers=headers)
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=str(e))

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # First try to find the problems section
    problems_section = soup.find('section', {'class': 'problems_solved_section'})
    if not problems_section:
        # Try to find the container with problem counts
        problems_section = soup.find('div', {'class': 'row problems-solved'})
    
    if not problems_section:
        # For debugging
        print("HTML Content:", response.text[:1000])  # Print first 1000 chars
        raise HTTPException(
            status_code=400,
            detail="Could not find problem statistics section on the page"
        )

    problem_difficulty_tags = ["School", "Basic", "Easy", "Medium", "Hard"]
    problem_counts = {tag: 0 for tag in problem_difficulty_tags}
    total_problems = 0

    # Try multiple patterns to find problem counts
    for difficulty in problem_difficulty_tags:
        # Try finding specific difficulty divs
        difficulty_div = problems_section.find('div', string=re.compile(difficulty, re.IGNORECASE))
        if difficulty_div:
            # Look for the count in the next sibling or parent
            count_text = difficulty_div.find_next('div').text if difficulty_div.find_next('div') else ''
            if not count_text:
                count_text = difficulty_div.parent.text if difficulty_div.parent else ''
            
            # Extract number from text
            numbers = re.findall(r'\d+', count_text)
            if numbers:
                count = int(numbers[0])
                problem_counts[difficulty] = count
                total_problems += count

    # If we haven't found any problems, try alternative parsing
    if total_problems == 0:
        # Look for any numbers following difficulty levels
        text = problems_section.get_text()
        for difficulty in problem_difficulty_tags:
            pattern = rf"{difficulty}[^\d]*(\d+)"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                count = int(match.group(1))
                problem_counts[difficulty] = count
                total_problems += count

    # If still no problems found, look for overall statistics
    if total_problems == 0:
        overall_stats = soup.find('div', {'class': 'score_cards_container'})
        if overall_stats:
            numbers = re.findall(r'\d+', overall_stats.get_text())
            if numbers:
                total_problems = sum(int(num) for num in numbers)
                # Distribute evenly if we only have total
                avg = total_problems // len(problem_difficulty_tags)
                problem_counts = {tag: avg for tag in problem_difficulty_tags}

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
    summary="Get User's Complete Statistics")
async def get_user_statistics(username: str):
    return await get_user_stats(username)

@app.get("/user/{username}/problems",
    tags=["Problem Analysis"],
    summary="Get User's Problem Solving Statistics")
async def get_problem_statistics(
    username: str,
    difficulty: Optional[str] = Query(None)
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
    summary="Get User's Progress Metrics")
async def get_progress_metrics(username: str):
    stats = await get_user_stats(username)
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

@app.get("/",
    tags=["General"],
    summary="API Documentation",
    description="Redirects to the API documentation page")
async def root():
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=8000)

