from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import Pagination, get_current_user, get_pagination
from app.models.user import User
from app.schemas.common import PaginationMeta
from app.schemas.favorite import FavoriteCreate, FavoriteRead
from app.services.favorite_service import FavoriteService

router = APIRouter()


@router.get("")
async def list_my_favorites(
    pagination: Pagination = Depends(get_pagination),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    service = FavoriteService(db)
    favorites, total = await service.list_mine(current_user, pagination.page, pagination.page_size)
    total_pages = (total + pagination.page_size - 1) // pagination.page_size if total else 0
    return {
        "data": [FavoriteRead.model_validate(f) for f in favorites],
        "meta": PaginationMeta(
            page=pagination.page, page_size=pagination.page_size, total=total, total_pages=total_pages
        ),
    }


@router.post("", status_code=201)
async def add_favorite(
    payload: FavoriteCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
) -> dict:
    service = FavoriteService(db)
    favorite = await service.add(payload.song_id, current_user)
    return {"data": FavoriteRead.model_validate(favorite)}


@router.delete("/{song_id}", status_code=204)
async def remove_favorite(
    song_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
) -> None:
    service = FavoriteService(db)
    await service.remove(song_id, current_user)
