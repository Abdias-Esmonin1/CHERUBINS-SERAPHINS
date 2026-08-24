from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rights_record import RightsRecord


class RightsRecordRepository:
    """Append-only : volontairement AUCUNE méthode update/delete —
    aucun endpoint ni service ne doit pouvoir modifier un enregistrement
    existant (Phase 7, portée validée)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, record: RightsRecord) -> RightsRecord:
        self._session.add(record)
        await self._session.flush()
        await self._session.refresh(record)
        return record

    async def list_paginated(
        self,
        page: int,
        page_size: int,
        lyrics_id: UUID | None = None,
        translation_id: UUID | None = None,
        action: str | None = None,
        performed_by_user_id: UUID | None = None,
    ) -> tuple[list[RightsRecord], int]:
        stmt = select(RightsRecord)
        if lyrics_id is not None:
            stmt = stmt.where(RightsRecord.lyrics_id == lyrics_id)
        if translation_id is not None:
            stmt = stmt.where(RightsRecord.translation_id == translation_id)
        if action is not None:
            stmt = stmt.where(RightsRecord.action == action)
        if performed_by_user_id is not None:
            stmt = stmt.where(RightsRecord.performed_by_user_id == performed_by_user_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(RightsRecord.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total
