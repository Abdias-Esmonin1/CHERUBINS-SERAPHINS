from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.language import Language


class LanguageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self, only_active: bool = False) -> list[Language]:
        stmt = select(Language).order_by(Language.name)
        if only_active:
            stmt = stmt.where(Language.is_active.is_(True))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, language_id: UUID) -> Language | None:
        result = await self._session.execute(select(Language).where(Language.id == language_id))
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Language | None:
        result = await self._session.execute(select(Language).where(Language.code == code))
        return result.scalar_one_or_none()

    async def create(self, language: Language) -> Language:
        self._session.add(language)
        await self._session.flush()
        await self._session.refresh(language)
        return language
