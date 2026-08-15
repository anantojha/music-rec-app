import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class RecommendationHistory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One row per 'generate recommendations' request. `taste_profile` stores the
    structured JSON GPT produced in pipeline Step 2, so past runs are reproducible
    and auditable without re-calling the LLM."""

    __tablename__ = "recommendation_history"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_playlist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False
    )
    taste_profile: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    user: Mapped["User"] = relationship(back_populates="recommendations")
    items: Mapped[list["RecommendationItem"]] = relationship(
        back_populates="recommendation", cascade="all, delete-orphan", order_by="RecommendationItem.rank"
    )


class RecommendationItem(UUIDPrimaryKeyMixin, Base):
    """A single recommended song within a RecommendationHistory batch (pipeline Step 4)."""

    __tablename__ = "recommendation_items"

    recommendation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recommendation_history.id", ondelete="CASCADE"), nullable=False
    )
    track_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    liked: Mapped[bool | None] = mapped_column(nullable=True)  # like/dislike, nice-to-have feature

    recommendation: Mapped["RecommendationHistory"] = relationship(back_populates="items")
    track: Mapped["Track"] = relationship()
