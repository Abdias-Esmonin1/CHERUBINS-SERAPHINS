from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Album(Base):
    __tablename__ = "albums"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    artist_id: Mapped[UUID] = mapped_column(ForeignKey("artists.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    release_year: Mapped[int | None] = mapped_column(SmallInteger)
    cover_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    artist: Mapped["Artist"] = relationship(back_populates="albums")
    songs: Mapped[list["Song"]] = relationship(back_populates="album")

    __table_args__ = (Index("idx_albums_artist_id", "artist_id"),)
