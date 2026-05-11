from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from models.canonical import make_envelope
from services import canonical_mapper
from services.heatmap import get_user_heatmap
from services.heatmap_window import normalize_view, window_heatmap


router = APIRouter(tags=["Canonical"])


@router.get("/{username}/heatmap")
async def get_submission_heatmap(
    username: str,
    view: str = Query("all", description="all | last_365 | year"),
    range: str | None = Query(default=None, description="Deprecated alias for view (all|last365days|year)"),
    year: int | None = Query(default=None, ge=2000, le=2100),
    month: int | None = Query(default=None, ge=1, le=12, description="Deprecated; not applied to the canonical block"),
):
    try:
        # ``range`` is the deprecated GFG param; ``view`` is the unified one.
        requested = range if range is not None else view
        view_n, year_n = normalize_view(requested, year)

        # Fetch the full history once and window locally so yearlyContributions
        # and availableYears always describe every year since account creation.
        heatmap_data = await get_user_heatmap(username, range_name="all")
        available_years = [int(y) for y in heatmap_data.get("availableYears", []) or []]
        heatmap = window_heatmap(
            canonical_mapper.heatmap_from(heatmap_data),
            view_n,
            year_n,
            available_years=available_years or None,
        )
        return make_envelope(username, heatmap)
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"error": True, "message": e.detail, "status_code": e.status_code, "endpoint": "heatmap"},
        )
