import uuid

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Album(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "albums"

    name: Mapped[str] = mapped_column(String(500), nullable=False)
    release_year: Mapped[int | None] = mapped_column(Integer, nullable=True)

    tracks: Mapped[list["Track"]] = relationship(back_populates="album")
