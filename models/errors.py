from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ErrorResponse(BaseModel):
    error: bool = True
    message: str
    status_code: int
    endpoint: str
