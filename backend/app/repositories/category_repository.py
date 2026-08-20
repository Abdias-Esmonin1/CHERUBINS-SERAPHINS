from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category


class CategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[Category]:
        result = await self._session.execute(select(Category).order_by(Category.name))
        return list(result.scalars().all())

    async def get_by_id(self, category_id: UUID) -> Category | None:
        result = await self._session.execute(select(Category).where(Category.id == category_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Category | None:
        result = await self._session.execute(select(Category).where(Category.name == name))
        return result.scalar_one_or_none()

    async def create(self, category: Category) -> Category:
        self._session.add(category)
        await self._session.flush()
        await self._session.refresh(category)
        return category
