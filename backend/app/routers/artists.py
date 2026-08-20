from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import Pagination, get_pagination, require_admin
from app.models.user import User
from app.schemas.artist import ArtistCreate, ArtistRead
from app.schemas.common import PaginationMeta
from app.services.catalog_service import CatalogService

router = APIRouter()


@router.get("")
async def list_artists(
    country: str | None = None,
    is_verified: bool | None = None,
    pagination: Pagination = Depends(get_pagination),
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = CatalogService(db)
    artists, total = await service.artists.list_paginated(
        pagination.page, pagination.page_size, country=country, is_verified=is_verified
    )
    total_pages = (total + pagination.page_size - 1) // pagination.page_size if total else 0
    return {
        "data": [ArtistRead.model_validate(a) for a in artists],
        "meta": PaginationMeta(
            page=pagination.page, page_size=pagination.page_size, total=total, total_pages=total_pages
        ),
    }


@router.get("/{slug}")
async def get_artist(slug: str, db: AsyncSession = Depends(get_db)) -> dict:
    service = CatalogService(db)
    artist = await service.get_artist_by_slug(slug)
    return {"data": ArtistRead.model_validate(artist)}


@router.post("", status_code=201)
async def create_artist(
    payload: ArtistCreate, db: AsyncSession = Depends(get_db), _admin: User = Depends(require_admin)
) -> dict:
    service = CatalogService(db)
    artist = await service.create_artist(payload)
    return {"data": ArtistRead.model_validate(artist)}
