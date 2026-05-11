from fastapi import APIRouter

from models.canonical import Contests, make_envelope


router = APIRouter(tags=["Canonical"])


@router.get("/{username}/contests")
async def get_contests(username: str):
    return make_envelope(username, Contests())
