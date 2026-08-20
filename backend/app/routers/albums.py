from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import Pagination, get_pagination, require_admin
from app.models.user import User
from app.schemas.album import AlbumCreate, AlbumRead
from app.schemas.common import PaginationMeta
from app.services.catalog_service import CatalogService

router = APIRouter()


@router.get("")
async def list_albums(
    artist_id: UUID | None = None,
    pagination: Pagination = Depends(get_pagination),
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = CatalogService(db)
    albums, total = await service.albums.list_paginated(pagination.page, pagination.page_size, artist_id=artist_id)
    total_pages = (total + pagination.page_size - 1) // pagination.page_size if total else 0
    return {
        "data": [AlbumRead.model_validate(a) for a in albums],
        "meta": PaginationMeta(
            page=pagination.page, page_size=pagination.page_size, total=total, total_pages=total_pages
        ),
    }


@router.get("/{album_id}")
async def get_album(album_id: UUID, db: AsyncSession = Depends(get_db)) -> dict:
    service = CatalogService(db)
    album = await service.get_album(album_id)
    return {"data": AlbumRead.model_validate(album)}


@router.post("", status_code=201)
async def create_album(
    payload: AlbumCreate, db: AsyncSession = Depends(get_db), _admin: User = Depends(require_admin)
) -> dict:
    service = CatalogService(db)
    album = await service.create_album(payload)
    return {"data": AlbumRead.model_validate(album)}
