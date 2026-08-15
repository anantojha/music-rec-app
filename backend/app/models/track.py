import uuid

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Track(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A single track, cached locally so the recommendation engine doesn't have to
    hit Spotify's API on every request. Audio-feature columns mirror what the
    engine extracts in Step 1 of the pipeline (see services/recommendation_engine.py).
    """

    __tablename__ = "tracks"

    name: Mapped[str] = mapped_column(String(500), nullable=False)
    artist_names: Mapped[list[str]] = mapped_column(ARRAY(String(255)), nullable=False, default=list)
    album_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("albums.id", ondelete="SET NULL"), nullable=True
    )

    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="spotify")
    provider_track_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Audio features used to build the playlist taste profile.
    tempo: Mapped[float | None] = mapped_column(Float, nullable=True)
    energy: Mapped[float | None] = mapped_column(Float, nullable=True)
    danceability: Mapped[float | None] = mapped_column(Float, nullable=True)
    acousticness: Mapped[float | None] = mapped_column(Float, nullable=True)
    popularity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    release_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    genres: Mapped[list[str]] = mapped_column(ARRAY(String(100)), nullable=False, default=list)

    album: Mapped["Album | None"] = relationship(back_populates="tracks")
    playlist_links: Mapped[list["PlaylistTrack"]] = relationship(back_populates="track")
