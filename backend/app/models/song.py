from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Song(Base):
    """Chanson référencée — peut exister sans paroles publiées (Song 1 -- 0..1 Lyrics).

    Référencer une chanson ne signifie pas publier ses paroles
    (Stratégie de contenu §3, §12) — la table `lyrics` sera ajoutée en
    Phase 4 avec sa propre règle de visibilité, indépendante de
    `Song.status`.
    """

    __tablename__ = "songs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(280), nullable=False, unique=True)
    artist_id: Mapped[UUID] = mapped_column(ForeignKey("artists.id", ondelete="RESTRICT"), nullable=False)
    album_id: Mapped[UUID | None] = mapped_column(ForeignKey("albums.id", ondelete="SET NULL"))
    category_id: Mapped[UUID | None] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"))
    original_language_id: Mapped[UUID] = mapped_column(
        ForeignKey("languages.id", ondelete="RESTRICT"), nullable=False
    )
    cover_url: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT", server_default="DRAFT")
    external_provider: Mapped[str | None] = mapped_column(String(50))
    external_id: Mapped[str | None] = mapped_column(String(255))
    external_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    artist: Mapped["Artist"] = relationship(back_populates="songs")
    album: Mapped["Album | None"] = relationship(back_populates="songs")
    category: Mapped["Category | None"] = relationship(back_populates="songs")
    original_language: Mapped["Language"] = relationship(back_populates="songs")

    __table_args__ = (
        CheckConstraint("status IN ('DRAFT', 'PUBLISHED', 'ARCHIVED')", name="ck_songs_status"),
        Index("idx_songs_artist_id", "artist_id"),
        Index("idx_songs_album_id", "album_id"),
        Index("idx_songs_category_id", "category_id"),
        Index("idx_songs_original_language_id", "original_language_id"),
        Index("idx_songs_status", "status"),
    )
