from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Lyrics(Base):
    """Paroles originales d'une chanson — Song 1 -- 0..1 Lyrics.

    Référencer une chanson ne signifie pas publier ses paroles
    (Stratégie de contenu §3, §12). Seul `authorization_status =
    AUTHORIZED` (et `expiration_date` non dépassée) rend le contenu
    visible publiquement — règle appliquée exclusivement côté service
    (`lyrics_service.py`), jamais ici ni côté frontend.

    Phase 4 (portée validée — Option A) : les transitions de statut
    (PENDING -> AUTHORIZED/REJECTED, AUTHORIZED -> REVOKED/EXPIRED) et
    leur traçabilité (`rights_records`) appartiennent à la Phase 7.
    Une parole soumise en Phase 4 reste donc `PENDING` jusqu'à
    l'implémentation de la modération admin.
    """

    __tablename__ = "lyrics"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    song_id: Mapped[UUID] = mapped_column(
        ForeignKey("songs.id", ondelete="RESTRICT"), nullable=False, unique=True
    )
    language_id: Mapped[UUID] = mapped_column(ForeignKey("languages.id", ondelete="RESTRICT"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    rights_holder: Mapped[str | None] = mapped_column(String(255))
    authorization_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING", server_default="PENDING"
    )
    authorization_reference: Mapped[str | None] = mapped_column(String(100))
    authorization_date: Mapped[date | None] = mapped_column(Date)
    expiration_date: Mapped[date | None] = mapped_column(Date)
    submitted_by_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    reviewed_by_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    song: Mapped["Song"] = relationship(back_populates="lyrics")
    language: Mapped["Language"] = relationship()
    submitted_by: Mapped["User | None"] = relationship(foreign_keys=[submitted_by_user_id])
    reviewed_by: Mapped["User | None"] = relationship(foreign_keys=[reviewed_by_user_id])
    translations: Mapped[list["Translation"]] = relationship(back_populates="lyrics")

    __table_args__ = (
        CheckConstraint(
            "source_type IN ('ORIGINAL', 'ARTIST', 'RIGHTS_HOLDER', 'LICENSE', 'PARTNER', "
            "'PUBLIC_DOMAIN', 'USER_SUBMITTED')",
            name="ck_lyrics_source_type",
        ),
        CheckConstraint(
            "authorization_status IN ('PENDING', 'AUTHORIZED', 'REJECTED', 'EXPIRED', 'REVOKED')",
            name="ck_lyrics_authorization_status",
        ),
        Index("idx_lyrics_authorization_status", "authorization_status"),
        Index("idx_lyrics_source_type", "source_type"),
        Index("idx_lyrics_submitted_by_user_id", "submitted_by_user_id"),
    )
