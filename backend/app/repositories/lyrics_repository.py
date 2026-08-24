from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.lyrics import Lyrics

_EAGER_LOAD = (selectinload(Lyrics.language),)


class LyricsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_song_id(self, song_id: UUID) -> Lyrics | None:
        result = await self._session.execute(
            select(Lyrics).where(Lyrics.song_id == song_id).options(*_EAGER_LOAD)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, lyrics_id: UUID) -> Lyrics | None:
        result = await self._session.execute(
            select(Lyrics).where(Lyrics.id == lyrics_id).options(*_EAGER_LOAD)
        )
        return result.scalar_one_or_none()

    async def list_by_submitter(
        self, submitted_by_user_id: UUID, page: int, page_size: int
    ) -> tuple[list[Lyrics], int]:
        stmt = select(Lyrics).where(Lyrics.submitted_by_user_id == submitted_by_user_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = (
            stmt.options(*_EAGER_LOAD)
            .order_by(Lyrics.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def list_by_status(self, status: str | None, page: int, page_size: int) -> tuple[list[Lyrics], int]:
        """Listing admin — tous statuts si `status` est None. Ajouté en
        Phase 7, extension non destructive (aucune méthode existante
        modifiée)."""
        stmt = select(Lyrics)
        if status is not None:
            stmt = stmt.where(Lyrics.authorization_status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = (
            stmt.options(*_EAGER_LOAD)
            .order_by(Lyrics.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def create(self, lyrics: Lyrics) -> Lyrics:
        self._session.add(lyrics)
        await self._session.flush()
        await self._session.refresh(lyrics)
        return lyrics
