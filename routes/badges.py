from fastapi import APIRouter

from models.canonical import Badges, make_envelope


router = APIRouter(tags=["Canonical"])


@router.get("/{username}/badges")
async def get_badges(username: str):
    return make_envelope(username, Badges())
