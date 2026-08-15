import uuid

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token
from app.db.database import get_db
from app.db.repositories import UserRepository
from app.models.user import User
from app.services.openai_service import OpenAIService
from app.services.spotify_service import SpotifyService


async def get_current_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise UnauthorizedError("Missing or malformed Authorization header.")

    token = authorization.split(" ", 1)[1]
    subject = decode_access_token(token)
    if not subject:
        raise UnauthorizedError("Invalid or expired access token.")

    user = await UserRepository(db).get_by_id(uuid.UUID(subject))
    if not user:
        raise UnauthorizedError("User for this token no longer exists.")
    return user


def get_spotify_service() -> SpotifyService:
    return SpotifyService()


def get_openai_service() -> OpenAIService:
    return OpenAIService()
