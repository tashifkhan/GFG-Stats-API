from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from models.canonical import make_envelope
from services import canonical_mapper


router = APIRouter(tags=["Canonical"])


@router.get("/{username}")
async def get_summary(username: str):
    try:
        card = await canonical_mapper.build_card(username, include_topics=False)
        legacy = {"userName": username, "totalProblemsSolved": card.stats.totalSolved}
        return make_envelope(username, canonical_mapper.summary_from(card), legacy=legacy)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"error": True, "message": e.detail, "status_code": e.status_code, "endpoint": "summary"})
