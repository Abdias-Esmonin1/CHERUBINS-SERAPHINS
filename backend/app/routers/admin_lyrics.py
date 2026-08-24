from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import Pagination, get_pagination, require_admin
from app.exceptions import NotFoundError
from app.models.user import User
from app.repositories.lyrics_repository import LyricsRepository
from app.schemas.common import PaginationMeta
from app.schemas.lyrics import LyricsOwnerRead
from app.schemas.rights_record import ModerationAuthorizeRequest, ModerationReasonRequest
from app.services.moderation_service import ModerationService

router = APIRouter()


@router.get("")
async def list_lyrics(
    status: str | None = None,
    pagination: Pagination = Depends(get_pagination),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict:
    repo = LyricsRepository(db)
    lyrics_list, total = await repo.list_by_status(status, pagination.page, pagination.page_size)
    total_pages = (total + pagination.page_size - 1) // pagination.page_size if total else 0
    return {
        "data": [LyricsOwnerRead.model_validate(lyrics) for lyrics in lyrics_list],
        "meta": PaginationMeta(
            page=pagination.page, page_size=pagination.page_size, total=total, total_pages=total_pages
        ),
    }


@router.get("/{lyrics_id}")
async def get_lyrics(lyrics_id: UUID, db: AsyncSession = Depends(get_db), _admin: User = Depends(require_admin)) -> dict:
    repo = LyricsRepository(db)
    lyrics = await repo.get_by_id(lyrics_id)
    if lyrics is None:
        raise NotFoundError("Paroles introuvables.", code="LYRICS_NOT_FOUND")
    return {"data": LyricsOwnerRead.model_validate(lyrics)}


@router.patch("/{lyrics_id}/authorize")
async def authorize_lyrics(
    lyrics_id: UUID,
    payload: ModerationAuthorizeRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> dict:
    service = ModerationService(db)
    lyrics = await service.authorize_lyrics(lyrics_id, payload, admin)
    return {"data": LyricsOwnerRead.model_validate(lyrics)}


@router.patch("/{lyrics_id}/reject")
async def reject_lyrics(
    lyrics_id: UUID,
    payload: ModerationReasonRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> dict:
    service = ModerationService(db)
    lyrics = await service.reject_lyrics(lyrics_id, payload.reason, admin)
    return {"data": LyricsOwnerRead.model_validate(lyrics)}


@router.patch("/{lyrics_id}/revoke")
async def revoke_lyrics(
    lyrics_id: UUID,
    payload: ModerationReasonRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> dict:
    service = ModerationService(db)
    lyrics = await service.revoke_lyrics(lyrics_id, payload.reason, admin)
    return {"data": LyricsOwnerRead.model_validate(lyrics)}
