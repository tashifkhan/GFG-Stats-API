from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class HeatmapEntry(BaseModel):
    date: str
    count: int

class UserHeatmap(BaseModel):
    userName: str
    range: str
    accountCreatedDate: str
    fromDate: str
    toDate: str
    availableYears: List[int]
    totalActiveDays: int
    totalSubmissions: int
    heatmap: List[HeatmapEntry]
