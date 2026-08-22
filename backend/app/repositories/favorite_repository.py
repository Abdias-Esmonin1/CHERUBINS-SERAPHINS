from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.favorite import Favorite
from app.models.song import Song

_EAGER_LOAD = (
    selectinload(Favorite.song).selectinload(Song.artist),
    selectinload(Favorite.song).selectinload(Song.album),
    selectinload(Favorite.song).selectinload(Song.category),
    selectinload(Favorite.song).selectinload(Song.original_language),
)


class FavoriteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_paginated(self, user_id: UUID, page: int, page_size: int) -> tuple[list[Favorite], int]:
        stmt = select(Favorite).where(Favorite.user_id == user_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = (
            stmt.options(*_EAGER_LOAD)
            .order_by(Favorite.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def get_by_id(self, favorite_id: UUID) -> Favorite | None:
        result = await self._session.execute(
            select(Favorite).where(Favorite.id == favorite_id).options(*_EAGER_LOAD)
        )
        return result.scalar_one_or_none()

    async def get_by_user_and_song(self, user_id: UUID, song_id: UUID) -> Favorite | None:
        result = await self._session.execute(
            select(Favorite).where(Favorite.user_id == user_id, Favorite.song_id == song_id)
        )
        return result.scalar_one_or_none()

    async def create(self, favorite: Favorite) -> Favorite:
        self._session.add(favorite)
        await self._session.flush()
        await self._session.refresh(favorite)
        return favorite

    async def delete(self, favorite: Favorite) -> None:
        await self._session.delete(favorite)
        await self._session.flush()
