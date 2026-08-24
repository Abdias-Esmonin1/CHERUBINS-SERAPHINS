from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import Pagination, get_pagination, require_admin
from app.models.user import User
from app.repositories.rights_record_repository import RightsRecordRepository
from app.schemas.common import PaginationMeta
from app.schemas.rights_record import RightsRecordRead

router = APIRouter()

# Aucun endpoint POST/PUT/PATCH/DELETE sur ce router — rights_records
# est append-only strict, alimenté exclusivement par
# moderation_service.py (Phase 7, portée validée).


@router.get("")
async def list_rights_records(
    lyrics_id: UUID | None = None,
    translation_id: UUID | None = None,
    action: str | None = None,
    performed_by_user_id: UUID | None = None,
    pagination: Pagination = Depends(get_pagination),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict:
    repo = RightsRecordRepository(db)
    records, total = await repo.list_paginated(
        pagination.page,
        pagination.page_size,
        lyrics_id=lyrics_id,
        translation_id=translation_id,
        action=action,
        performed_by_user_id=performed_by_user_id,
    )
    total_pages = (total + pagination.page_size - 1) // pagination.page_size if total else 0
    return {
        "data": [RightsRecordRead.model_validate(r) for r in records],
        "meta": PaginationMeta(
            page=pagination.page, page_size=pagination.page_size, total=total, total_pages=total_pages
        ),
    }
