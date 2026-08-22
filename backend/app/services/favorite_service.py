"""Service Favorite — ajout, suppression, consultation des favoris.

Cf. Livrable 2 §2.1 : un service ne lève que des exceptions métier,
jamais de HTTPException. Toujours scopé à `current_user.id` — aucun
`user_id` n'est jamais accepté depuis le client (protection IDOR par
construction, même principe que /lyrics/mine et /translations/mine).

Décision Phase 6 (signalée en amont, non tranchée silencieusement) :
aucune restriction sur `Song.status` — la validation ne porte que sur
l'existence de la chanson (`SongRepository.get_by_id`, sans filtre de
statut, même comportement que pour Lyrics/Translations).
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictError, NotFoundError
from app.models.favorite import Favorite
from app.models.user import User
from app.repositories.favorite_repository import FavoriteRepository
from app.repositories.song_repository import SongRepository


class FavoriteService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.favorites = FavoriteRepository(session)
        self._songs = SongRepository(session)

    async def add(self, song_id: UUID, current_user: User) -> Favorite:
        if await self._songs.get_by_id(song_id) is None:
            raise NotFoundError("Chanson introuvable.", code="SONG_NOT_FOUND")
        if await self.favorites.get_by_user_and_song(current_user.id, song_id) is not None:
            raise ConflictError("Cette chanson est déjà dans vos favoris.", code="ALREADY_FAVORITED")

        favorite = Favorite(user_id=current_user.id, song_id=song_id)
        favorite = await self.favorites.create(favorite)
        await self._session.commit()
        return await self.favorites.get_by_id(favorite.id)  # recharge avec song eager-loaded

    async def remove(self, song_id: UUID, current_user: User) -> None:
        favorite = await self.favorites.get_by_user_and_song(current_user.id, song_id)
        if favorite is None:
            raise NotFoundError("Ce favori n'existe pas.", code="FAVORITE_NOT_FOUND")
        await self.favorites.delete(favorite)
        await self._session.commit()

    async def list_mine(self, current_user: User, page: int, page_size: int) -> tuple[list[Favorite], int]:
        return await self.favorites.list_paginated(current_user.id, page, page_size)
