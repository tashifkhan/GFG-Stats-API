from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class UserProblemInfo(BaseModel):
    question: str
    questionUrl: str
    difficulty: str

class UserStats(BaseModel):
    userName: str
    totalProblemsSolved: int = 0
    School: int = 0
    Basic: int = 0
    Easy: int = 0
    Medium: int = 0
    Hard: int = 0
