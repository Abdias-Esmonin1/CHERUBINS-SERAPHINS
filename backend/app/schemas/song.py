from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ArtistBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    slug: str


class AlbumBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str


class CategoryBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str


class LanguageBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    code: str
    name: str


class SongRead(BaseModel):
    """Fiche chanson (Livrable 3 §3.1/§3.3).

    Note Phase 3 : le champ `lyrics_available` prévu par le Livrable 4
    (wireframes) n'est PAS encore inclus ici — la table `lyrics`
    n'existe pas avant la Phase 4. Il sera ajouté à ce schéma en
    Phase 4, sans modification de structure ailleurs (limitation
    documentée, pas une décision métier).
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    slug: str
    status: str
    cover_url: str | None = None
    external_provider: str | None = None
    external_id: str | None = None
    external_url: str | None = None
    artist: ArtistBrief
    album: AlbumBrief | None = None
    category: CategoryBrief | None = None
    original_language: LanguageBrief


class SongCreate(BaseModel):
    """Contrat exact — Livrable 3 §3.4. `status` n'est pas fourni par le
    client : forcé à DRAFT à la création (Livrable 1 §3.8)."""

    title: str = Field(min_length=1, max_length=255)
    artist_id: UUID
    album_id: UUID | None = None
    category_id: UUID | None = None
    original_language_id: UUID
    cover_url: str | None = None
    external_provider: str | None = Field(default=None, max_length=50)
    external_id: str | None = Field(default=None, max_length=255)
    external_url: str | None = None


class SongUpdate(BaseModel):
    """Contrat — Livrable 3 §3.5 : `status` modifiable ici, y compris
    par un ADMIN, indépendamment du statut des paroles (règle validée,
    Livrable 3 §7 arbitrage final)."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    album_id: UUID | None = None
    category_id: UUID | None = None
    cover_url: str | None = None
    status: str | None = None
    external_provider: str | None = Field(default=None, max_length=50)
    external_id: str | None = Field(default=None, max_length=255)
    external_url: str | None = None
