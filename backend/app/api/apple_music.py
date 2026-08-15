from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/apple-music", tags=["apple-music"])


@router.get("/connect")
async def connect(current_user: User = Depends(get_current_user)) -> dict:
    """Placeholder endpoint. Apple Music is supported at the abstraction level
    (see services/music_provider.py + services/apple_music_service.py) but not
    yet wired up end-to-end. Returns 501 until AppleMusicService is completed."""
    return {
        "status": "not_implemented",
        "message": "Apple Music support is planned. The provider abstraction is in place; "
        "OAuth + API calls are not yet implemented.",
    }
