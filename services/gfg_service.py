from fastapi import HTTPException
import httpx
from bs4 import BeautifulSoup
import re
import json
from typing import Dict, Any
from config import settings

async def get_user_stats(username: str) -> Dict:
    """
    Fetch and parse user statistics from GeeksForGeeks profile page.
    This is the original fallback method.
    """
    url = f"https://www.geeksforgeeks.org/user/{username}/"
    
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            try:
                headers = {"User-Agent": settings.user_agent}
                response = await client.get(url, headers=headers, timeout=settings.request_timeout)
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

async def get_detailed_user_data(username: str) -> Dict[str, Any]:
    """
    Fetch and parse detailed user data from GeeksForGeeks practice page.
    This function extracts data from JSON embedded in a script tag.
    """
    # Protect against favicon.ico requests that can cause errors
    if username == "favicon.ico":
        raise HTTPException(status_code=400, detail="Invalid username: favicon.ico is not a valid GeeksForGeeks username")
        
    base_url = f'https://auth.geeksforgeeks.org/user/{username}/practice/'
    
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            try:
                headers = {"User-Agent": settings.user_agent}
                response = await client.get(base_url, headers=headers, timeout=settings.request_timeout)
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

    # Ensure consistent data types for fields that might be integers or strings
    general_info = {
        "userName": username,
        "fullName": user_info.get("name", ""),
        "profilePicture": user_info.get("profile_image_url", ""),
        "institute": user_info.get("institute_name", ""),
        "instituteRank": str(user_info.get("institute_rank", "")),
        "currentStreak": str(user_info.get("pod_solved_longest_streak", "00")),
        "maxStreak": str(user_info.get("pod_solved_global_longest_streak", "00")),
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
