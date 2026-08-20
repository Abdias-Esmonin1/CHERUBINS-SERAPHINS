from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import Pagination, get_pagination, require_admin
from app.models.user import User
from app.schemas.common import PaginationMeta
from app.schemas.song import SongCreate, SongRead, SongUpdate
from app.services.catalog_service import CatalogService

router = APIRouter()


def _envelope(songs, total: int, pagination: Pagination) -> dict:
    total_pages = (total + pagination.page_size - 1) // pagination.page_size if total else 0
    return {
        "data": [SongRead.model_validate(s) for s in songs],
        "meta": PaginationMeta(
            page=pagination.page, page_size=pagination.page_size, total=total, total_pages=total_pages
        ),
    }


@router.get("")
async def list_songs(
    category_id: UUID | None = None,
    language_id: UUID | None = None,
    artist_id: UUID | None = None,
    pagination: Pagination = Depends(get_pagination),
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = CatalogService(db)
    songs, total = await service.songs.list_paginated(
        pagination.page, pagination.page_size, category_id=category_id, language_id=language_id, artist_id=artist_id
    )
    return _envelope(songs, total, pagination)


@router.get("/search")
async def search_songs(
    q: str = Query(min_length=1),
    category_id: UUID | None = None,
    language_id: UUID | None = None,
    pagination: Pagination = Depends(get_pagination),
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = CatalogService(db)
    songs, total = await service.songs.search(
        q, pagination.page, pagination.page_size, category_id=category_id, language_id=language_id
    )
    return _envelope(songs, total, pagination)


@router.get("/{slug}")
async def get_song(slug: str, db: AsyncSession = Depends(get_db)) -> dict:
    service = CatalogService(db)
    song = await service.get_song_by_slug(slug)
    return {"data": SongRead.model_validate(song)}


@router.post("", status_code=201)
async def create_song(
    payload: SongCreate, db: AsyncSession = Depends(get_db), _admin: User = Depends(require_admin)
) -> dict:
    service = CatalogService(db)
    song = await service.create_song(payload)
    return {"data": SongRead.model_validate(song)}


@router.put("/{song_id}")
async def update_song(
    song_id: UUID,
    payload: SongUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict:
    service = CatalogService(db)
    song = await service.update_song(song_id, payload)
    return {"data": SongRead.model_validate(song)}
