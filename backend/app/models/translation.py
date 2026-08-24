from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Translation(Base):
    """Traduction d'une parole originale — Lyrics 1 -- N Translation.

    Cycle de vie des droits totalement indépendant de celui de la
    parole originale (`Lyrics.authorization_status`) : une traduction
    peut être `AUTHORIZED` alors que l'original ne l'est pas, et
    inversement. Seul `authorization_status = AUTHORIZED` (et non
    expiré) rend la traduction visible publiquement — règle appliquée
    exclusivement côté service (`translation_service.py`).

    `submitted_by_user_id`/`reviewed_by_user_id` sont la source de
    vérité de la propriété (jamais déduits de `rights_records`,
    décision validée en conception).

    Phase 5 (portée validée, symétrique à l'Option A de la Phase 4
    pour Lyrics) : aucune transition de statut ni `rights_records` en
    Phase 5 — réservés à la Phase 7.

    `authorization_reference`/`authorization_date` ajoutés en Phase 7
    (Option A validée) : jugés non requis en Phase 5, ils deviennent
    nécessaires au contrat de l'endpoint `authorize` de la
    modération admin.
    """

    __tablename__ = "translations"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    lyrics_id: Mapped[UUID] = mapped_column(ForeignKey("lyrics.id", ondelete="RESTRICT"), nullable=False)
    target_language_id: Mapped[UUID] = mapped_column(
        ForeignKey("languages.id", ondelete="RESTRICT"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    translation_type: Mapped[str] = mapped_column(String(20), nullable=False)
    authorization_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING", server_default="PENDING"
    )
    authorization_reference: Mapped[str | None] = mapped_column(String(100))
    authorization_date: Mapped[date | None] = mapped_column(Date)
    expiration_date: Mapped[date | None] = mapped_column(Date)
    source_url: Mapped[str | None] = mapped_column(Text)
    rights_holder: Mapped[str | None] = mapped_column(String(255))
    submitted_by_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    reviewed_by_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    lyrics: Mapped["Lyrics"] = relationship(back_populates="translations")
    target_language: Mapped["Language"] = relationship()
    submitted_by: Mapped["User | None"] = relationship(foreign_keys=[submitted_by_user_id])
    reviewed_by: Mapped["User | None"] = relationship(foreign_keys=[reviewed_by_user_id])

    __table_args__ = (
        UniqueConstraint("lyrics_id", "target_language_id", name="uq_translations_lyrics_language"),
        CheckConstraint(
            "translation_type IN ('OFFICIAL', 'AUTHOR', 'HUMAN', 'AI_GENERATED')",
            name="ck_translations_type",
        ),
        CheckConstraint(
            "authorization_status IN ('PENDING', 'AUTHORIZED', 'REJECTED', 'EXPIRED', 'REVOKED')",
            name="ck_translations_authorization_status",
        ),
        Index("idx_translations_lyrics_id", "lyrics_id"),
        Index("idx_translations_target_language_id", "target_language_id"),
        Index("idx_translations_authorization_status", "authorization_status"),
        Index("idx_translations_submitted_by_user_id", "submitted_by_user_id"),
    )
