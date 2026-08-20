from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.artist import Artist
from app.models.song import Song

_EAGER_LOAD = (
    selectinload(Song.artist),
    selectinload(Song.album),
    selectinload(Song.category),
    selectinload(Song.original_language),
)


class SongRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_paginated(
        self,
        page: int,
        page_size: int,
        category_id: UUID | None = None,
        language_id: UUID | None = None,
        artist_id: UUID | None = None,
    ) -> tuple[list[Song], int]:
        stmt = select(Song).where(Song.status == "PUBLISHED", Song.deleted_at.is_(None))
        if category_id is not None:
            stmt = stmt.where(Song.category_id == category_id)
        if language_id is not None:
            stmt = stmt.where(Song.original_language_id == language_id)
        if artist_id is not None:
            stmt = stmt.where(Song.artist_id == artist_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = (
            stmt.options(*_EAGER_LOAD)
            .order_by(Song.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def search(
        self,
        query: str,
        page: int,
        page_size: int,
        category_id: UUID | None = None,
        language_id: UUID | None = None,
    ) -> tuple[list[Song], int]:
        """Recherche par correspondance partielle sur le titre et le nom
        de l'artiste (ILIKE). Ne recherche PAS encore dans les paroles
        (`lyrics` n'existe pas avant la Phase 4) — voir limitation
        documentée dans le rapport de fin de phase.
        """
        pattern = f"%{query}%"
        stmt = (
            select(Song)
            .join(Artist, Song.artist_id == Artist.id)
            .where(
                Song.status == "PUBLISHED",
                Song.deleted_at.is_(None),
                or_(Song.title.ilike(pattern), Artist.name.ilike(pattern)),
            )
        )
        if category_id is not None:
            stmt = stmt.where(Song.category_id == category_id)
        if language_id is not None:
            stmt = stmt.where(Song.original_language_id == language_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.options(*_EAGER_LOAD).offset((page - 1) * page_size).limit(page_size)
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def get_by_slug(self, slug: str) -> Song | None:
        result = await self._session.execute(
            select(Song)
            .where(Song.slug == slug, Song.status == "PUBLISHED", Song.deleted_at.is_(None))
            .options(*_EAGER_LOAD)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, song_id: UUID) -> Song | None:
        result = await self._session.execute(
            select(Song).where(Song.id == song_id).options(*_EAGER_LOAD)
        )
        return result.scalar_one_or_none()

    async def slug_exists(self, slug: str) -> bool:
        result = await self._session.execute(select(Song.id).where(Song.slug == slug))
        return result.scalar_one_or_none() is not None

    async def create(self, song: Song) -> Song:
        self._session.add(song)
        await self._session.flush()
        await self._session.refresh(song)
        return song
