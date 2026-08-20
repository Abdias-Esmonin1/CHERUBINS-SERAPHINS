from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.album import Album


class AlbumRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_paginated(
        self, page: int, page_size: int, artist_id: UUID | None = None
    ) -> tuple[list[Album], int]:
        stmt = select(Album)
        if artist_id is not None:
            stmt = stmt.where(Album.artist_id == artist_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(Album.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def get_by_id(self, album_id: UUID) -> Album | None:
        result = await self._session.execute(
            select(Album).where(Album.id == album_id).options(selectinload(Album.artist))
        )
        return result.scalar_one_or_none()

    async def create(self, album: Album) -> Album:
        self._session.add(album)
        await self._session.flush()
        await self._session.refresh(album)
        return album
