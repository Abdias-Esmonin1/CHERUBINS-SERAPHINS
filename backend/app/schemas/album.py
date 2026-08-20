from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AlbumRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    artist_id: UUID
    title: str
    release_year: int | None = None
    cover_url: str | None = None


class AlbumCreate(BaseModel):
    """Contrat exact — Livrable 3 §5.3."""

    artist_id: UUID
    title: str = Field(min_length=1, max_length=255)
    release_year: int | None = Field(default=None, ge=1900, le=2200)
    cover_url: str | None = None


class AlbumUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    release_year: int | None = Field(default=None, ge=1900, le=2200)
    cover_url: str | None = None
