"""
Import every model here so SQLAlchemy's mapper registry can resolve the string-based
relationship() references (e.g. Mapped["User"]) declared in each model module.
Anything that imports app.db.database.Base should import this package first,
which app/main.py and alembic/env.py both do.
"""
from app.models.album import Album  # noqa: F401
from app.models.oauth_account import MusicProvider, OAuthAccount  # noqa: F401
from app.models.playlist import Playlist, PlaylistTrack  # noqa: F401
from app.models.recommendation import RecommendationHistory, RecommendationItem  # noqa: F401
from app.models.track import Track  # noqa: F401
from app.models.user import User  # noqa: F401

__all__ = [
    "Album",
    "MusicProvider",
    "OAuthAccount",
    "Playlist",
    "PlaylistTrack",
    "RecommendationHistory",
    "RecommendationItem",
    "Track",
    "User",
]
