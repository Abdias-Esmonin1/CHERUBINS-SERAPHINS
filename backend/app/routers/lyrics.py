from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import Pagination, get_current_user, get_current_user_optional, get_pagination
from app.models.user import User
from app.schemas.common import PaginationMeta
from app.schemas.lyrics import LyricsCreate, LyricsOwnerRead, LyricsUpdate
from app.services.lyrics_service import LyricsService

router = APIRouter()


@router.post("", status_code=201)
async def submit_lyrics(
    payload: LyricsCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
) -> dict:
    service = LyricsService(db)
    lyrics = await service.submit(payload, current_user)
    return {"data": LyricsOwnerRead.model_validate(lyrics)}


@router.get("/mine")
async def list_my_lyrics(
    pagination: Pagination = Depends(get_pagination),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    service = LyricsService(db)
    lyrics_list, total = await service.list_mine(current_user, pagination.page, pagination.page_size)
    total_pages = (total + pagination.page_size - 1) // pagination.page_size if total else 0
    return {
        "data": [LyricsOwnerRead.model_validate(lyrics) for lyrics in lyrics_list],
        "meta": PaginationMeta(
            page=pagination.page, page_size=pagination.page_size, total=total, total_pages=total_pages
        ),
    }


@router.get("/song/{song_id}")
async def get_lyrics_for_song(
    song_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> dict:
    service = LyricsService(db)
    result = await service.get_visibility(song_id, current_user)
    return {"data": result}


@router.put("/{lyrics_id}")
async def update_lyrics(
    lyrics_id: UUID,
    payload: LyricsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    service = LyricsService(db)
    lyrics = await service.update(lyrics_id, payload, current_user)
    return {"data": LyricsOwnerRead.model_validate(lyrics)}
