"""Service Translation — logique métier de soumission, visibilité et
édition des traductions.

Cf. Livrable 2 §2.1 : un service ne lève que des exceptions métier,
jamais de HTTPException. La visibilité est déterminée INDÉPENDAMMENT
pour chaque traduction d'une même parole (des traductions différentes
peuvent avoir des auteurs différents et des statuts différents).

La soumission d'une traduction est autorisée même si les paroles
originales ne sont pas encore `AUTHORIZED` (décision validée en
conception) — leurs cycles de droits sont indépendants.

Phase 5 (portée validée — symétrique à l'Option A de la Phase 4) :
aucune transition de statut n'est possible ici (PATCH
.../authorize|reject|revoke = Phase 7). Une traduction soumise reste
`PENDING` jusqu'à l'implémentation de la modération admin.
"""

from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.translation import Translation
from app.models.user import User
from app.repositories.language_repository import LanguageRepository
from app.repositories.lyrics_repository import LyricsRepository
from app.repositories.translation_repository import TranslationRepository
from app.schemas.song import LanguageBrief
from app.schemas.translation import (
    TranslationCreate,
    TranslationOwnerRead,
    TranslationUpdate,
    TranslationVisibilityItem,
)


class TranslationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.translations = TranslationRepository(session)
        self._lyrics = LyricsRepository(session)
        self._languages = LanguageRepository(session)

    # ------------------------------------------------------------ Submit

    async def submit(self, payload: TranslationCreate, current_user: User) -> Translation:
        if await self._lyrics.get_by_id(payload.lyrics_id) is None:
            raise NotFoundError("Paroles introuvables.", code="LYRICS_NOT_FOUND")
        if await self._languages.get_by_id(payload.target_language_id) is None:
            raise NotFoundError("Langue introuvable.", code="LANGUAGE_NOT_FOUND")
        if (
            await self.translations.get_by_lyrics_and_language(payload.lyrics_id, payload.target_language_id)
            is not None
        ):
            raise ConflictError(
                "Une traduction existe déjà pour cette langue cible.", code="TRANSLATION_ALREADY_EXISTS"
            )

        translation = Translation(
            lyrics_id=payload.lyrics_id,
            target_language_id=payload.target_language_id,
            content=payload.content,
            translation_type=payload.translation_type,
            source_url=payload.source_url,
            rights_holder=payload.rights_holder,
            authorization_status="PENDING",  # forcé, jamais fourni par le client
            submitted_by_user_id=current_user.id,  # forcé, jamais fourni par le client
        )
        translation = await self.translations.create(translation)
        await self._session.commit()
        return await self.translations.get_by_id(translation.id)  # recharge avec target_language eager-loaded

    # --------------------------------------------------------- Visibility

    async def get_visibility_list(
        self, lyrics_id: UUID, current_user: User | None, target_language_id: UUID | None = None
    ) -> list[TranslationVisibilityItem | TranslationOwnerRead]:
        if await self._lyrics.get_by_id(lyrics_id) is None:
            raise NotFoundError("Paroles introuvables.", code="LYRICS_NOT_FOUND")

        translations = await self.translations.list_by_lyrics_id(lyrics_id, target_language_id)

        is_admin = current_user is not None and current_user.role.name == "ADMIN"
        results: list[TranslationVisibilityItem | TranslationOwnerRead] = []
        for translation in translations:
            is_author = current_user is not None and translation.submitted_by_user_id == current_user.id
            if is_admin or is_author:
                results.append(TranslationOwnerRead.model_validate(translation))
            elif self._is_publicly_visible(translation):
                results.append(
                    TranslationVisibilityItem(
                        available=True,
                        target_language=LanguageBrief.model_validate(translation.target_language),
                        translation_type=translation.translation_type,
                        content=translation.content,
                    )
                )
            else:
                results.append(
                    TranslationVisibilityItem(
                        available=False,
                        target_language=LanguageBrief.model_validate(translation.target_language),
                    )
                )
        return results

    @staticmethod
    def _is_publicly_visible(translation: Translation) -> bool:
        if translation.authorization_status != "AUTHORIZED":
            return False
        if translation.expiration_date is not None and translation.expiration_date < date.today():
            return False
        return True

    # -------------------------------------------------------------- Edit

    async def update(self, translation_id: UUID, payload: TranslationUpdate, current_user: User) -> Translation:
        translation = await self.translations.get_by_id(translation_id)
        if translation is None:
            raise NotFoundError("Traduction introuvable.", code="TRANSLATION_NOT_FOUND")

        is_admin = current_user.role.name == "ADMIN"
        is_author = translation.submitted_by_user_id == current_user.id

        if not (is_admin or is_author):
            raise ForbiddenError("Vous ne pouvez pas modifier cette traduction.", code="FORBIDDEN")

        # Même restriction que pour Lyrics : édition de contenu limitée
        # à PENDING, pour l'auteur ET l'ADMIN (les transitions de statut
        # sont un mécanisme séparé, Phase 7).
        if translation.authorization_status != "PENDING":
            raise ConflictError("Cette traduction a déjà été traitée.", code="TRANSLATION_ALREADY_REVIEWED")

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(translation, field, value)

        await self._session.commit()
        return await self.translations.get_by_id(translation.id)

    # -------------------------------------------------------------- Mine

    async def list_mine(self, current_user: User, page: int, page_size: int) -> tuple[list[Translation], int]:
        return await self.translations.list_by_submitter(current_user.id, page, page_size)
