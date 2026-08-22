from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Favorite(Base):
    """Chanson mise en favori par un utilisateur — ressource strictement
    privée à son propriétaire, jamais consultable par un tiers.

    Contrairement à `Lyrics`/`Translation`, aucune notion de
    statut/droits : pas de visibilité publique différenciée, pas
    d'auteur distinct de l'utilisateur (le propriétaire EST
    l'utilisateur connecté). `ON DELETE CASCADE` sur les deux FK
    (contrairement à `RESTRICT` ailleurs) : supprimer un utilisateur
    ou une chanson supprime les favoris associés, cohérent avec le MCD
    validé (Livrable 1) — aucune traçabilité de droits n'est en jeu
    ici.

    Décision prise (Phase 6, signalée en amont, non tranchée
    silencieusement) : aucune restriction sur `Song.status` — une
    chanson DRAFT/ARCHIVED peut être mise en favori si son UUID est
    connu, la validation ne porte que sur l'existence de la chanson.
    """

    __tablename__ = "favorites"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    song_id: Mapped[UUID] = mapped_column(ForeignKey("songs.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user: Mapped["User"] = relationship()
    song: Mapped["Song"] = relationship()

    __table_args__ = (
        UniqueConstraint("user_id", "song_id", name="uq_favorites_user_song"),
        Index("idx_favorites_user_id", "user_id"),
        Index("idx_favorites_song_id", "song_id"),
    )
