from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from models.canonical import make_envelope
from services import canonical_mapper
from services.profile import get_detailed_user_data


router = APIRouter(tags=["Canonical"])


@router.get("/{username}/stats")
async def get_stats(username: str):
    try:
        detailed_data = await get_detailed_user_data(username)
        return make_envelope(username, await canonical_mapper.stats_from(detailed_data))
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"error": True, "message": e.detail, "status_code": e.status_code, "endpoint": "stats"})
