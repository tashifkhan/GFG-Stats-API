from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from models.canonical import make_envelope
from services import canonical_mapper
from services.profile import get_detailed_user_data


router = APIRouter(tags=["Canonical"])


@router.get("/{username}/topics")
async def get_topics(username: str):
    try:
        detailed_data = await get_detailed_user_data(username)
        stats = await canonical_mapper.stats_from(detailed_data)
        return make_envelope(username, stats.topicAnalysis)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"error": True, "message": e.detail, "status_code": e.status_code, "endpoint": "topics"})
