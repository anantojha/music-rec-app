import enum
import uuid
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class MusicProvider(str, enum.Enum):
    """The abstraction point that lets us add Apple Music later without touching
    the recommendation engine or DB schema — see services/music_provider.py."""

    SPOTIFY = "spotify"
    APPLE_MUSIC = "apple_music"


class OAuthAccount(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A user's linked account with an external music provider.

    Access/refresh tokens are stored encrypted at rest (see core/security.py::TokenCipher).
    Callers should always go through services/*_service.py rather than reading
    encrypted_access_token directly.
    """

    __tablename__ = "oauth_accounts"
    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_provider_account"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[MusicProvider] = mapped_column(Enum(MusicProvider, values_callable=lambda enum_cls: [e.value for e in enum_cls]), nullable=False)
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)

    encrypted_access_token: Mapped[str] = mapped_column(Text, nullable=False)
    encrypted_refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="oauth_accounts")
