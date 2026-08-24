"""Service de modération — authorize/reject/revoke pour Lyrics ET
Translation, avec traçabilité systématique via RightsRecord.

Cf. Livrable 2 §2.1 : un service ne lève que des exceptions métier,
jamais de HTTPException. Toute la logique de transition et de
validation ADMIN vit ici — jamais dans les routers (consigne §12).

Cohérence transactionnelle stricte : la mise à jour de la ressource
(Lyrics/Translation) et la création du RightsRecord correspondant se
font dans la MÊME transaction (un seul `commit()` par appel). Une
transition invalide lève une exception AVANT toute modification et
AVANT toute création de RightsRecord — donc aucun état incohérent
n'est possible : soit les deux écritures aboutissent ensemble, soit
aucune n'a lieu.

`EXPIRED` reste calculé à la lecture (déjà en place dans
lyrics_service/translation_service) — aucun scheduler introduit ici,
et ce module n'écrit jamais littéralement 'EXPIRED' en base. Pour la
transition `EXPIRED -> AUTHORIZED` ("restore"), le statut *effectif*
d'une ressource est donc calculé de la même façon que pour la
visibilité publique (`authorization_status == 'AUTHORIZED'` ET
`expiration_date` dépassée => statut effectif `'EXPIRED'`) plutôt que
de lire littéralement la colonne stockée, qui ne contient jamais
cette valeur.
"""

from datetime import date
from typing import Literal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictError, NotFoundError
from app.models.lyrics import Lyrics
from app.models.rights_record import RightsRecord
from app.models.translation import Translation
from app.models.user import User
from app.repositories.lyrics_repository import LyricsRepository
from app.repositories.rights_record_repository import RightsRecordRepository
from app.repositories.translation_repository import TranslationRepository
from app.schemas.rights_record import ModerationAuthorizeRequest

# Transitions autorisées, identiques pour lyrics et translations
# (consigne, transitions validées). Basées sur le statut EFFECTIF
# (cf. _effective_status), pas uniquement la colonne brute.
_AUTHORIZE_FROM = {"PENDING", "EXPIRED"}
_REJECT_FROM = {"PENDING"}
_REVOKE_FROM = {"AUTHORIZED"}

TargetType = Literal["lyrics", "translation"]


def _effective_status(resource: Lyrics | Translation) -> str:
    """Statut effectif pour la validation des transitions — identique
    à la règle de visibilité déjà en place : un enregistrement stocké
    `AUTHORIZED` dont `expiration_date` est dépassée est considéré
    `EXPIRED`, bien que jamais littéralement écrit ainsi en base."""
    if resource.authorization_status == "AUTHORIZED" and resource.expiration_date is not None:
        if resource.expiration_date < date.today():
            return "EXPIRED"
    return resource.authorization_status


class ModerationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._lyrics_repo = LyricsRepository(session)
        self._translation_repo = TranslationRepository(session)
        self._rights_records = RightsRecordRepository(session)

    # ---------------------------------------------------------- Lyrics

    async def authorize_lyrics(
        self, lyrics_id: UUID, payload: ModerationAuthorizeRequest, current_user: User
    ) -> Lyrics:
        lyrics = await self._get_lyrics_or_404(lyrics_id)
        previous_status = self._check_transition(_effective_status(lyrics), _AUTHORIZE_FROM)

        lyrics.authorization_status = "AUTHORIZED"
        lyrics.authorization_reference = payload.authorization_reference
        lyrics.authorization_date = payload.authorization_date
        lyrics.expiration_date = payload.expiration_date
        lyrics.reviewed_by_user_id = current_user.id

        await self._record(
            lyrics_id=lyrics.id,
            action="VALIDATED",
            previous_status=previous_status,
            new_status="AUTHORIZED",
            reason=None,
            performed_by_user_id=current_user.id,
        )
        await self._session.commit()
        return await self._lyrics_repo.get_by_id(lyrics.id)

    async def reject_lyrics(self, lyrics_id: UUID, reason: str, current_user: User) -> Lyrics:
        lyrics = await self._get_lyrics_or_404(lyrics_id)
        previous_status = self._check_transition(lyrics.authorization_status, _REJECT_FROM)

        lyrics.authorization_status = "REJECTED"
        lyrics.reviewed_by_user_id = current_user.id

        await self._record(
            lyrics_id=lyrics.id,
            action="REJECTED",
            previous_status=previous_status,
            new_status="REJECTED",
            reason=reason,
            performed_by_user_id=current_user.id,
        )
        await self._session.commit()
        return await self._lyrics_repo.get_by_id(lyrics.id)

    async def revoke_lyrics(self, lyrics_id: UUID, reason: str, current_user: User) -> Lyrics:
        lyrics = await self._get_lyrics_or_404(lyrics_id)
        previous_status = self._check_transition(lyrics.authorization_status, _REVOKE_FROM)

        lyrics.authorization_status = "REVOKED"
        lyrics.reviewed_by_user_id = current_user.id

        await self._record(
            lyrics_id=lyrics.id,
            action="REVOKED",
            previous_status=previous_status,
            new_status="REVOKED",
            reason=reason,
            performed_by_user_id=current_user.id,
        )
        await self._session.commit()
        return await self._lyrics_repo.get_by_id(lyrics.id)

    # ------------------------------------------------------- Translation

    async def authorize_translation(
        self, translation_id: UUID, payload: ModerationAuthorizeRequest, current_user: User
    ) -> Translation:
        translation = await self._get_translation_or_404(translation_id)
        previous_status = self._check_transition(_effective_status(translation), _AUTHORIZE_FROM)

        translation.authorization_status = "AUTHORIZED"
        translation.authorization_reference = payload.authorization_reference
        translation.authorization_date = payload.authorization_date
        translation.expiration_date = payload.expiration_date
        translation.reviewed_by_user_id = current_user.id

        await self._record(
            translation_id=translation.id,
            action="VALIDATED",
            previous_status=previous_status,
            new_status="AUTHORIZED",
            reason=None,
            performed_by_user_id=current_user.id,
        )
        await self._session.commit()
        return await self._translation_repo.get_by_id(translation.id)

    async def reject_translation(self, translation_id: UUID, reason: str, current_user: User) -> Translation:
        translation = await self._get_translation_or_404(translation_id)
        previous_status = self._check_transition(translation.authorization_status, _REJECT_FROM)

        translation.authorization_status = "REJECTED"
        translation.reviewed_by_user_id = current_user.id

        await self._record(
            translation_id=translation.id,
            action="REJECTED",
            previous_status=previous_status,
            new_status="REJECTED",
            reason=reason,
            performed_by_user_id=current_user.id,
        )
        await self._session.commit()
        return await self._translation_repo.get_by_id(translation.id)

    async def revoke_translation(self, translation_id: UUID, reason: str, current_user: User) -> Translation:
        translation = await self._get_translation_or_404(translation_id)
        previous_status = self._check_transition(translation.authorization_status, _REVOKE_FROM)

        translation.authorization_status = "REVOKED"
        translation.reviewed_by_user_id = current_user.id

        await self._record(
            translation_id=translation.id,
            action="REVOKED",
            previous_status=previous_status,
            new_status="REVOKED",
            reason=reason,
            performed_by_user_id=current_user.id,
        )
        await self._session.commit()
        return await self._translation_repo.get_by_id(translation.id)

    # -------------------------------------------------------------- Utils

    async def _get_lyrics_or_404(self, lyrics_id: UUID) -> Lyrics:
        lyrics = await self._lyrics_repo.get_by_id(lyrics_id)
        if lyrics is None:
            raise NotFoundError("Paroles introuvables.", code="LYRICS_NOT_FOUND")
        return lyrics

    async def _get_translation_or_404(self, translation_id: UUID) -> Translation:
        translation = await self._translation_repo.get_by_id(translation_id)
        if translation is None:
            raise NotFoundError("Traduction introuvable.", code="TRANSLATION_NOT_FOUND")
        return translation

    @staticmethod
    def _check_transition(current_status: str, allowed_from: set[str]) -> str:
        """Vérifie que la transition est autorisée depuis le statut
        actuel. Lève AVANT toute modification/écriture — garantit
        qu'aucun état partiel n'est jamais créé."""
        if current_status not in allowed_from:
            raise ConflictError(
                f"Transition invalide depuis le statut '{current_status}'.", code="INVALID_TRANSITION"
            )
        return current_status

    async def _record(
        self,
        *,
        action: str,
        previous_status: str,
        new_status: str,
        reason: str | None,
        performed_by_user_id: UUID,
        lyrics_id: UUID | None = None,
        translation_id: UUID | None = None,
    ) -> RightsRecord:
        record = RightsRecord(
            lyrics_id=lyrics_id,
            translation_id=translation_id,
            action=action,
            previous_status=previous_status,
            new_status=new_status,
            reason=reason,
            performed_by_user_id=performed_by_user_id,
        )
        return await self._rights_records.create(record)
