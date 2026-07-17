from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from models.canonical import make_envelope
from services import canonical_mapper
from services.profile import get_detailed_user_data
from services.stats_svg import error_svg_response, parse_exclude_list, stats_svg_response


router = APIRouter(tags=["Canonical"])


@router.get("/{username}/stats/svg", summary="Stats SVG card")
async def get_stats_svg(
    username: str,
    theme: str = Query("dark", description="Card theme: dark or light"),
    exclude: str | None = Query(
        None,
        description="Comma-separated topics to exclude from the topic bars",
    ),
):
    try:
        detailed_data = await get_detailed_user_data(username)
        data = await canonical_mapper.stats_from(detailed_data)
        return stats_svg_response(
            "gfg",
            username,
            data,
            theme=theme,
            exclude=parse_exclude_list(exclude),
        )
    except HTTPException as e:
        return error_svg_response(
            str(e.detail),
            platform="gfg",
            username=username,
            theme=theme,
            status_code=e.status_code,
        )


@router.get("/{username}/stats")
async def get_stats(username: str):
    try:
        detailed_data = await get_detailed_user_data(username)
        return make_envelope(username, await canonical_mapper.stats_from(detailed_data))
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": True,
                "message": e.detail,
                "status_code": e.status_code,
                "endpoint": "stats",
            },
        )
