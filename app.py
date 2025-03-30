from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Dict, Optional, List
import httpx
from bs4 import BeautifulSoup
import re
import json

app = FastAPI(
    title="GeeksForGeeks Analytics API",
    description="An API for analyzing GeeksForGeeks user problem-solving statistics",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path
        }
    )

async def get_user_stats(username: str) -> Dict:
    """
    Fetch and parse user statistics from GeeksForGeeks profile page.
    This function implements the parsing logic similar to the Express.js app.
    """
    url = f"https://www.geeksforgeeks.org/user/{username}/"
    
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                response = await client.get(url, headers=headers, timeout=10.0)
                response.raise_for_status()
            except httpx.TimeoutException:
                raise HTTPException(status_code=504, detail=f"Request to GeeksForGeeks timed out. Please try again later.")
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise HTTPException(status_code=404, detail=f"User '{username}' not found on GeeksForGeeks")
                else:
                    raise HTTPException(
                        status_code=e.response.status_code, 
                        detail=f"GeeksForGeeks API error: {e.response.reason_phrase}"
                    )
            except httpx.RequestError:
                raise HTTPException(
                    status_code=503, 
                    detail="Failed to connect to GeeksForGeeks. The service might be down or your internet connection is unstable."
                )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    soup = BeautifulSoup(response.text, 'html.parser')
    
    problem_difficulty_tags = ["School", "Basic", "Easy", "Medium", "Hard"]
    values = {tag: 0 for tag in problem_difficulty_tags}
    total_problems_solved = 0
    
    data = soup.select('.problemNavbar_head__cKSRi')
    
    if data:
        raw_data = data[0].text
        k = 0
        for i in range(len(raw_data)):
            if raw_data[i] == '(':
                temp_start = i + 1
                while i < len(raw_data) and raw_data[i] != ')':
                    i += 1
                if i < len(raw_data):
                    try:
                        temp_problems = int(raw_data[temp_start:i])
                        if k < len(problem_difficulty_tags):
                            values[problem_difficulty_tags[k]] = temp_problems
                            total_problems_solved += temp_problems
                            k += 1
                    except ValueError:
                        pass
    
    if total_problems_solved == 0:
        problems_section = soup.find('section', {'class': 'problems_solved_section'})
        if not problems_section:
            problems_section = soup.find('div', {'class': 'row problems-solved'})
        
        if problems_section:
            for difficulty in problem_difficulty_tags:
                difficulty_div = problems_section.find('div', string=re.compile(difficulty, re.IGNORECASE))
                if difficulty_div:
                    count_text = difficulty_div.find_next('div').text if difficulty_div.find_next('div') else ''
                    if not count_text:
                        count_text = difficulty_div.parent.text if difficulty_div.parent else ''
                    
                    numbers = re.findall(r'\d+', count_text)
                    if numbers:
                        count = int(numbers[0])
                        values[difficulty] = count
                        total_problems_solved += count
    
    if total_problems_solved == 0:
        text = soup.get_text()
        for difficulty in problem_difficulty_tags:
            pattern = rf"{difficulty}[^\d]*(\d+)"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                count = int(match.group(1))
                values[difficulty] = count
                total_problems_solved += count
    
    if total_problems_solved == 0:
        overall_stats = soup.find('div', {'class': 'score_cards_container'})
        if overall_stats:
            numbers = re.findall(r'\d+', overall_stats.get_text())
            if numbers and len(numbers) > 0:
                total_problems_solved = sum(int(num) for num in numbers)
                avg = total_problems_solved // len(problem_difficulty_tags)
                for tag in problem_difficulty_tags:
                    values[tag] = avg
    
    if total_problems_solved == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No problem solving data found for user '{username}'. The user may not have solved any problems or the GeeksForGeeks profile structure has changed."
        )

    values["userName"] = username
    values["totalProblemsSolved"] = total_problems_solved
    
    return values

async def get_detailed_user_data(username: str) -> Dict:
    """
    Fetch and parse detailed user data from GeeksForGeeks practice page.
    This function extracts data from JSON embedded in a script tag.
    """
    base_url = f'https://auth.geeksforgeeks.org/user/{username}/practice/'
    
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                response = await client.get(base_url, headers=headers, timeout=10.0)
                response.raise_for_status()
            except httpx.TimeoutException:
                raise HTTPException(status_code=504, detail=f"Request to GeeksForGeeks timed out. Please try again later.")
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise HTTPException(status_code=404, detail=f"User '{username}' not found on GeeksForGeeks")
                else:
                    raise HTTPException(
                        status_code=e.response.status_code, 
                        detail=f"GeeksForGeeks API error: {e.response.reason_phrase}"
                    )
            except httpx.RequestError:
                raise HTTPException(
                    status_code=503, 
                    detail="Failed to connect to GeeksForGeeks. The service might be down or your internet connection is unstable."
                )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    soup = BeautifulSoup(response.text, 'html.parser')

    script_tag = soup.find("script", id="__NEXT_DATA__", attrs={"type": "application/json"})
    if not script_tag:
        raise HTTPException(
            status_code=422,
            detail=f"Could not extract data for user '{username}'. GeeksForGeeks may have changed their page structure."
        )

    try:
        user_data = json.loads(script_tag.string)
        
        if "props" not in user_data or "pageProps" not in user_data["props"]:
            raise HTTPException(
                status_code=404,
                detail=f"User data not found for '{username}'. The user may not exist or GeeksForGeeks has changed their data format."
            )
            
        user_info = user_data["props"]["pageProps"].get("userInfo")
        if not user_info:
            raise HTTPException(
                status_code=404,
                detail=f"User profile information not found for '{username}'."
            )
            
        user_submissions = user_data["props"]["pageProps"].get("userSubmissionsInfo")
        if not user_submissions:
            user_submissions = {}
            
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=422,
            detail="Failed to parse user data: Invalid JSON format in GeeksForGeeks response."
        )
    except KeyError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to access required data field: {str(e)}. GeeksForGeeks may have changed their data structure."
        )

    general_info = {
        "userName": username,
        "fullName": user_info.get("name", ""),
        "profilePicture": user_info.get("profile_image_url", ""),
        "institute": user_info.get("institute_name", ""),
        "instituteRank": user_info.get("institute_rank", ""),
        "currentStreak": user_info.get("pod_solved_longest_streak", "00"),
        "maxStreak": user_info.get("pod_solved_global_longest_streak", "00"),
        "codingScore": user_info.get("score", 0),
        "monthlyScore": user_info.get("monthly_score", 0),
        "totalProblemsSolved": user_info.get("total_problems_solved", 0),
    }

    solved_stats = {}
    all_problems = []
    
    for difficulty, problems in user_submissions.items():
        questions = []
        for details in problems.values():
            question_info = {
                "question": details["pname"],
                "questionUrl": f"https://practice.geeksforgeeks.org/problems/{details['slug']}",
                "difficulty": difficulty
            }
            questions.append(question_info)
            all_problems.append(question_info)
            
        solved_stats[difficulty.lower()] = {"count": len(questions), "questions": questions}

    return {
        "info": general_info,
        "solvedStats": solved_stats,
        "allProblems": all_problems
    }

@app.get("/{username}/profile",
    tags=["User Profile"],
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

@app.get("/{username}/solved-problems",
    tags=["Problem Analysis"],
    summary="Get User's Solved Problems",
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

@app.get("/{username}",
    tags=["User Stats"],
    summary="Get GeeksForGeeks User Stats",
    responses={
        200: {"description": "User statistics summary"},
        404: {"description": "User not found"},
        503: {"description": "GeeksForGeeks service unavailable"},
        504: {"description": "Request timeout"}
    })
async def get_stats_by_path(username: str):
    """
    Get user stats using username directly in the path.
    Example: /adarshsharc3pj
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

@app.get("/",
    tags=["Documentation"],
    summary="API Documentation")
async def root():
    """Redirect to the API documentation page"""
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=8000)

