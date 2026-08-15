import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Playlist(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "playlists"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="spotify")
    provider_playlist_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    user: Mapped["User"] = relationship(back_populates="playlists")
    track_links: Mapped[list["PlaylistTrack"]] = relationship(
        back_populates="playlist", cascade="all, delete-orphan", order_by="PlaylistTrack.position"
    )


class PlaylistTrack(Base):
    """Association table between playlists and tracks, preserving track order."""

    __tablename__ = "playlist_track"

    playlist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("playlists.id", ondelete="CASCADE"), primary_key=True
    )
    track_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tracks.id", ondelete="CASCADE"), primary_key=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    playlist: Mapped["Playlist"] = relationship(back_populates="track_links")
    track: Mapped["Track"] = relationship(back_populates="playlist_links")
