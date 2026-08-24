from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class RightsRecord(Base):
    """Journal d'audit des transitions de droits — append-only strict.

    Cible polymorphe : exactement une des deux FK (`lyrics_id` XOR
    `translation_id`) est renseignée, jamais les deux, jamais aucune
    (contrainte CHECK). Aucune méthode `update`/`delete` n'existe sur
    le repository associé ; aucun endpoint `PUT`/`PATCH`/`DELETE`
    n'existe sur `/admin/rights-records` — la table n'est modifiable
    qu'en ajout (Phase 7, portée validée).

    Chaque transition valide sur `Lyrics`/`Translation` (authorize,
    reject, revoke) crée exactement un `RightsRecord`, dans la même
    transaction que la mise à jour de la ressource concernée
    (`moderation_service.py`) — jamais l'un sans l'autre.

    `action` ne couvre que les 3 transitions pilotées par un ADMIN via
    `moderation_service.py` : `VALIDATED` (authorize, qu'il s'agisse
    de PENDING->AUTHORIZED ou EXPIRED->AUTHORIZED), `REJECTED`,
    `REVOKED`. L'événement `SUBMITTED` (création initiale d'une
    parole/traduction) n'est PAS rétroactivement tracé ici — cela
    nécessiterait de modifier `lyrics_service.submit()` et
    `translation_service.submit()` (Phases 4-5, déjà testés), ce qui
    n'est pas indispensable au fonctionnement de la Phase 7 et sort du
    périmètre validé (limitation documentée, pas un oubli).
    """

    __tablename__ = "rights_records"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    lyrics_id: Mapped[UUID | None] = mapped_column(ForeignKey("lyrics.id", ondelete="RESTRICT"))
    translation_id: Mapped[UUID | None] = mapped_column(ForeignKey("translations.id", ondelete="RESTRICT"))
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    previous_status: Mapped[str | None] = mapped_column(String(20))
    new_status: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    performed_by_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    lyrics: Mapped["Lyrics | None"] = relationship()
    translation: Mapped["Translation | None"] = relationship()
    performed_by: Mapped["User | None"] = relationship()

    __table_args__ = (
        CheckConstraint(
            "(lyrics_id IS NOT NULL AND translation_id IS NULL) OR "
            "(lyrics_id IS NULL AND translation_id IS NOT NULL)",
            name="ck_rights_records_exactly_one_target",
        ),
        CheckConstraint(
            "action IN ('VALIDATED', 'REJECTED', 'REVOKED')",
            name="ck_rights_records_action",
        ),
        Index("idx_rights_records_lyrics_id", "lyrics_id"),
        Index("idx_rights_records_translation_id", "translation_id"),
        Index("idx_rights_records_action", "action"),
        Index("idx_rights_records_performed_by_user_id", "performed_by_user_id"),
    )
