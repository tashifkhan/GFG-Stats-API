from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from models.canonical import make_envelope
from services import canonical_mapper
from services.profile import get_detailed_user_data


router = APIRouter(tags=["Canonical"])


@router.get("/{username}/profile")
async def get_user_profile(username: str):
    try:
        detailed_data = await get_detailed_user_data(username)
        for key in ["userName", "fullName", "profilePicture", "institute", "instituteRank", "currentStreak", "maxStreak"]:
            if key in detailed_data["info"] and detailed_data["info"][key] is None:
                detailed_data["info"][key] = ""
        data = canonical_mapper.profile_from(detailed_data, username)
        return make_envelope(username, data)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"error": True, "message": e.detail, "status_code": e.status_code, "endpoint": "profile"})
