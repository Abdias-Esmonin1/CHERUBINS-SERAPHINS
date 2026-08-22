from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.translation import Translation

_EAGER_LOAD = (selectinload(Translation.target_language),)


class TranslationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_lyrics_id(
        self, lyrics_id: UUID, target_language_id: UUID | None = None
    ) -> list[Translation]:
        stmt = select(Translation).where(Translation.lyrics_id == lyrics_id)
        if target_language_id is not None:
            stmt = stmt.where(Translation.target_language_id == target_language_id)
        stmt = stmt.options(*_EAGER_LOAD)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_lyrics_and_language(self, lyrics_id: UUID, target_language_id: UUID) -> Translation | None:
        result = await self._session.execute(
            select(Translation).where(
                Translation.lyrics_id == lyrics_id, Translation.target_language_id == target_language_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, translation_id: UUID) -> Translation | None:
        result = await self._session.execute(
            select(Translation).where(Translation.id == translation_id).options(*_EAGER_LOAD)
        )
        return result.scalar_one_or_none()

    async def list_by_submitter(
        self, submitted_by_user_id: UUID, page: int, page_size: int
    ) -> tuple[list[Translation], int]:
        stmt = select(Translation).where(Translation.submitted_by_user_id == submitted_by_user_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = (
            stmt.options(*_EAGER_LOAD)
            .order_by(Translation.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def create(self, translation: Translation) -> Translation:
        self._session.add(translation)
        await self._session.flush()
        await self._session.refresh(translation)
        return translation
