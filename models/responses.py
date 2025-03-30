from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator

class ErrorResponse(BaseModel):
    error: bool = True
    message: str
    status_code: int
    endpoint: str

class UserProblemInfo(BaseModel):
    question: str
    questionUrl: str
    difficulty: str

class UserProfile(BaseModel):
    userName: str
    fullName: str = ""
    profilePicture: str = ""
    institute: str = ""
    instituteRank: Union[str, int] = ""
    currentStreak: Union[str, int] = "00"
    maxStreak: Union[str, int] = "00"
    codingScore: int = 0
    monthlyScore: int = 0
    totalProblemsSolved: int = 0

    # Convert numeric values to strings for consistency
    @validator('instituteRank', 'currentStreak', 'maxStreak', pre=True)
    def convert_to_string(cls, value):
        if value is None:
            return ""
        return str(value)

class UserStats(BaseModel):
    userName: str
    totalProblemsSolved: int = 0
    School: int = 0
    Basic: int = 0
    Easy: int = 0
    Medium: int = 0
    Hard: int = 0

class SolvedProblems(BaseModel):
    userName: str
    totalProblemsSolved: int
    problemsByDifficulty: Dict[str, int]
    problems: List[UserProblemInfo]

class DetailedUserData(BaseModel):
    info: UserProfile
    solvedStats: Dict[str, Dict[str, Any]]
    allProblems: List[UserProblemInfo]
