from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import Pagination, get_pagination, require_admin
from app.exceptions import NotFoundError
from app.models.user import User
from app.repositories.translation_repository import TranslationRepository
from app.schemas.common import PaginationMeta
from app.schemas.rights_record import ModerationAuthorizeRequest, ModerationReasonRequest
from app.schemas.translation import TranslationOwnerRead
from app.services.moderation_service import ModerationService

router = APIRouter()


@router.get("")
async def list_translations(
    status: str | None = None,
    pagination: Pagination = Depends(get_pagination),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict:
    repo = TranslationRepository(db)
    translations, total = await repo.list_by_status(status, pagination.page, pagination.page_size)
    total_pages = (total + pagination.page_size - 1) // pagination.page_size if total else 0
    return {
        "data": [TranslationOwnerRead.model_validate(t) for t in translations],
        "meta": PaginationMeta(
            page=pagination.page, page_size=pagination.page_size, total=total, total_pages=total_pages
        ),
    }


@router.get("/{translation_id}")
async def get_translation(
    translation_id: UUID, db: AsyncSession = Depends(get_db), _admin: User = Depends(require_admin)
) -> dict:
    repo = TranslationRepository(db)
    translation = await repo.get_by_id(translation_id)
    if translation is None:
        raise NotFoundError("Traduction introuvable.", code="TRANSLATION_NOT_FOUND")
    return {"data": TranslationOwnerRead.model_validate(translation)}


@router.patch("/{translation_id}/authorize")
async def authorize_translation(
    translation_id: UUID,
    payload: ModerationAuthorizeRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> dict:
    service = ModerationService(db)
    translation = await service.authorize_translation(translation_id, payload, admin)
    return {"data": TranslationOwnerRead.model_validate(translation)}


@router.patch("/{translation_id}/reject")
async def reject_translation(
    translation_id: UUID,
    payload: ModerationReasonRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> dict:
    service = ModerationService(db)
    translation = await service.reject_translation(translation_id, payload.reason, admin)
    return {"data": TranslationOwnerRead.model_validate(translation)}


@router.patch("/{translation_id}/revoke")
async def revoke_translation(
    translation_id: UUID,
    payload: ModerationReasonRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> dict:
    service = ModerationService(db)
    translation = await service.revoke_translation(translation_id, payload.reason, admin)
    return {"data": TranslationOwnerRead.model_validate(translation)}
