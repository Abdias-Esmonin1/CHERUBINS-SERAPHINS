"""Service Lyrics — logique métier de soumission, visibilité et édition
des paroles.

Cf. Livrable 2 §2.1 : un service ne lève que des exceptions métier,
jamais de HTTPException. Règle de visibilité appliquée exclusivement
ici (jamais côté router ni frontend) : seul `authorization_status =
AUTHORIZED` et non expiré est exposé au public ; l'auteur et l'ADMIN
voient toujours le contenu réel de la soumission.

Phase 4 (portée validée — Option A) : aucune transition de statut
n'est possible ici (PATCH .../authorize|reject|revoke = Phase 7). Une
parole soumise reste `PENDING` jusqu'à l'implémentation de la
modération admin.
"""

from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.lyrics import Lyrics
from app.models.user import User
from app.repositories.language_repository import LanguageRepository
from app.repositories.lyrics_repository import LyricsRepository
from app.repositories.song_repository import SongRepository
from app.schemas.lyrics import LyricsCreate, LyricsOwnerRead, LyricsUpdate, LyricsVisibilityRead
from app.schemas.song import LanguageBrief


class LyricsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.lyrics = LyricsRepository(session)
        self._songs = SongRepository(session)
        self._languages = LanguageRepository(session)

    # ------------------------------------------------------------ Submit

    async def submit(self, payload: LyricsCreate, current_user: User) -> Lyrics:
        song = await self._songs.get_by_id(payload.song_id)
        if song is None:
            raise NotFoundError("Chanson introuvable.", code="SONG_NOT_FOUND")
        if await self._languages.get_by_id(payload.language_id) is None:
            raise NotFoundError("Langue introuvable.", code="LANGUAGE_NOT_FOUND")
        if await self.lyrics.get_by_song_id(payload.song_id) is not None:
            raise ConflictError(
                "Des paroles existent déjà pour cette chanson.", code="LYRICS_ALREADY_EXISTS"
            )

        lyrics = Lyrics(
            song_id=payload.song_id,
            language_id=payload.language_id,
            content=payload.content,
            source_type=payload.source_type,
            source_url=payload.source_url,
            rights_holder=payload.rights_holder,
            authorization_status="PENDING",  # forcé, jamais fourni par le client
            submitted_by_user_id=current_user.id,  # forcé, jamais fourni par le client
        )
        lyrics = await self.lyrics.create(lyrics)
        await self._session.commit()
        return await self.lyrics.get_by_id(lyrics.id)  # recharge avec language eager-loaded

    # --------------------------------------------------------- Visibility

    async def get_visibility(self, song_id: UUID, current_user: User | None) -> LyricsVisibilityRead | LyricsOwnerRead:
        song = await self._songs.get_by_id(song_id)
        if song is None:
            raise NotFoundError("Chanson introuvable.", code="SONG_NOT_FOUND")

        lyrics = await self.lyrics.get_by_song_id(song_id)
        if lyrics is None:
            return LyricsVisibilityRead(available=False)

        is_admin = current_user is not None and current_user.role.name == "ADMIN"
        is_author = current_user is not None and lyrics.submitted_by_user_id == current_user.id

        if is_admin or is_author:
            return LyricsOwnerRead.model_validate(lyrics)

        if self._is_publicly_visible(lyrics):
            return LyricsVisibilityRead(
                available=True, language=LanguageBrief.model_validate(lyrics.language), content=lyrics.content
            )
        return LyricsVisibilityRead(available=False)

    @staticmethod
    def _is_publicly_visible(lyrics: Lyrics) -> bool:
        if lyrics.authorization_status != "AUTHORIZED":
            return False
        if lyrics.expiration_date is not None and lyrics.expiration_date < date.today():
            return False
        return True

    # -------------------------------------------------------------- Edit

    async def update(self, lyrics_id: UUID, payload: LyricsUpdate, current_user: User) -> Lyrics:
        lyrics = await self.lyrics.get_by_id(lyrics_id)
        if lyrics is None:
            raise NotFoundError("Paroles introuvables.", code="LYRICS_NOT_FOUND")

        is_admin = current_user.role.name == "ADMIN"
        is_author = lyrics.submitted_by_user_id == current_user.id

        if not (is_admin or is_author):
            raise ForbiddenError("Vous ne pouvez pas modifier ces paroles.", code="FORBIDDEN")

        # Édition (contenu) restreinte à PENDING pour l'auteur ET
        # l'ADMIN — les transitions de statut (Phase 7) sont un
        # mécanisme séparé de cette édition de contenu (conforme au
        # contrat initial : "un ADMIN ou l'auteur peuvent corriger le
        # contenu tant que le statut est PENDING").
        if lyrics.authorization_status != "PENDING":
            raise ConflictError("Ces paroles ont déjà été traitées.", code="LYRICS_ALREADY_REVIEWED")

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(lyrics, field, value)

        await self._session.commit()
        return await self.lyrics.get_by_id(lyrics.id)

    # -------------------------------------------------------------- Mine

    async def list_mine(self, current_user: User, page: int, page_size: int) -> tuple[list[Lyrics], int]:
        return await self.lyrics.list_by_submitter(current_user.id, page, page_size)
