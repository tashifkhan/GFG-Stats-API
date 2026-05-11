from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class SolvedProblems(BaseModel):
    userName: str
    totalProblemsSolved: int
    problemsByDifficulty: Dict[str, int]
    problems: List[UserProblemInfo]
