from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import Pagination, get_current_user, get_current_user_optional, get_pagination
from app.models.user import User
from app.schemas.common import PaginationMeta
from app.schemas.translation import TranslationCreate, TranslationOwnerRead, TranslationUpdate
from app.services.translation_service import TranslationService

router = APIRouter()


@router.post("", status_code=201)
async def submit_translation(
    payload: TranslationCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
) -> dict:
    service = TranslationService(db)
    translation = await service.submit(payload, current_user)
    return {"data": TranslationOwnerRead.model_validate(translation)}


@router.get("/mine")
async def list_my_translations(
    pagination: Pagination = Depends(get_pagination),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    service = TranslationService(db)
    translations, total = await service.list_mine(current_user, pagination.page, pagination.page_size)
    total_pages = (total + pagination.page_size - 1) // pagination.page_size if total else 0
    return {
        "data": [TranslationOwnerRead.model_validate(t) for t in translations],
        "meta": PaginationMeta(
            page=pagination.page, page_size=pagination.page_size, total=total, total_pages=total_pages
        ),
    }


@router.get("/lyrics/{lyrics_id}")
async def get_translations_for_lyrics(
    lyrics_id: UUID,
    target_language_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> dict:
    service = TranslationService(db)
    result = await service.get_visibility_list(lyrics_id, current_user, target_language_id)
    return {"data": result}


@router.put("/{translation_id}")
async def update_translation(
    translation_id: UUID,
    payload: TranslationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    service = TranslationService(db)
    translation = await service.update(translation_id, payload, current_user)
    return {"data": TranslationOwnerRead.model_validate(translation)}
