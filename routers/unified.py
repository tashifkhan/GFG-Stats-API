"""Canonical unified endpoints shared across all stats services.

Adds ``/{username}/stats``, ``/{username}/contests``, ``/{username}/rating``,
``/{username}/badges`` and the aggregated ``/{username}/card`` for GeeksforGeeks.
Contests / rating / badges are always empty (not exposed publicly by GFG).
See ../UNIFIED_SCHEMA.md.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from models.unified import UnifiedBadges, UnifiedContests, UnifiedRating, make_envelope
from services import unified_mapper
from services.gfg_service import get_detailed_user_data

router = APIRouter(tags=["Unified"])


def _error(e: HTTPException, endpoint: str) -> JSONResponse:
    return JSONResponse(
        status_code=e.status_code,
        content={"error": True, "message": e.detail, "status_code": e.status_code, "endpoint": endpoint},
    )


@router.get("/{username}/stats", summary="Unified problem-solving stats")
async def unified_stats(username: str):
    try:
        detailed_data = await get_detailed_user_data(username)
        return make_envelope(username, unified_mapper.stats_from(detailed_data))
    except HTTPException as e:
        return _error(e, "stats")


@router.get("/{username}/contests", summary="Unified contests (empty for GFG)")
async def unified_contests(username: str):
    return make_envelope(username, UnifiedContests())


@router.get("/{username}/rating", summary="Unified rating (empty for GFG)")
async def unified_rating(username: str):
    return make_envelope(username, UnifiedRating())


@router.get("/{username}/badges", summary="Unified badges (empty for GFG)")
async def unified_badges(username: str):
    return make_envelope(username, UnifiedBadges())


@router.get("/{username}/card", summary="Aggregated unified profile card")
async def unified_card(username: str):
    try:
        return make_envelope(username, await unified_mapper.build_card(username))
    except HTTPException as e:
        return _error(e, "card")
