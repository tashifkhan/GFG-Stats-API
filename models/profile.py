from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

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

class DetailedUserData(BaseModel):
    info: UserProfile
    solvedStats: Dict[str, Dict[str, Any]]
    allProblems: List[UserProblemInfo]
