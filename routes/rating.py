from fastapi import APIRouter

from models.canonical import Rating, make_envelope


router = APIRouter(tags=["Canonical"])


@router.get("/{username}/rating")
async def get_rating(username: str):
    return make_envelope(username, Rating())
