from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ArtistRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    biography: str | None = None
    country: str | None = None
    image_url: str | None = None
    official_links: dict | None = None
    is_verified: bool


class ArtistCreate(BaseModel):
    """Contrat exact — Livrable 3 §4.3 : pas de `slug` (généré côté serveur)."""

    name: str = Field(min_length=1, max_length=200)
    biography: str | None = None
    country: str | None = Field(default=None, max_length=100)
    image_url: str | None = None
    official_links: dict | None = None


class ArtistUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    biography: str | None = None
    country: str | None = Field(default=None, max_length=100)
    image_url: str | None = None
    official_links: dict | None = None
    is_verified: bool | None = None
