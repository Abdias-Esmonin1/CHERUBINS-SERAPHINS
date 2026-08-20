from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artist import Artist


class ArtistRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_paginated(
        self,
        page: int,
        page_size: int,
        country: str | None = None,
        is_verified: bool | None = None,
    ) -> tuple[list[Artist], int]:
        stmt = select(Artist).where(Artist.deleted_at.is_(None))
        if country is not None:
            stmt = stmt.where(Artist.country == country)
        if is_verified is not None:
            stmt = stmt.where(Artist.is_verified == is_verified)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(Artist.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def get_by_slug(self, slug: str) -> Artist | None:
        result = await self._session.execute(
            select(Artist).where(Artist.slug == slug, Artist.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, artist_id: UUID) -> Artist | None:
        result = await self._session.execute(select(Artist).where(Artist.id == artist_id))
        return result.scalar_one_or_none()

    async def slug_exists(self, slug: str) -> bool:
        result = await self._session.execute(select(Artist.id).where(Artist.slug == slug))
        return result.scalar_one_or_none() is not None

    async def create(self, artist: Artist) -> Artist:
        self._session.add(artist)
        await self._session.flush()
        await self._session.refresh(artist)
        return artist
