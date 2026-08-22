"""Schémas Pydantic pour Lyrics.

Deux formes de sortie distinctes, jamais mélangées :
- LyricsVisibilityRead : ce qu'un visiteur public / autre USER reçoit
  (GET /lyrics/song/{id}) — ne contient structurellement AUCUN champ
  interne (statut, source, détenteur des droits, auteur...).
- LyricsOwnerRead : vue enrichie réservée à l'auteur de la soumission
  et à l'ADMIN (POST /lyrics, PUT /lyrics/{id}, GET /lyrics/mine, et
  GET /lyrics/song/{id} lorsque l'appelant est l'auteur/ADMIN).

Cette séparation est structurelle (deux classes différentes), pas une
simple omission conditionnelle de champs à l'exécution — conforme au
principe déjà appliqué à LyricsPublicRead/LyricsAdminRead (Livrable 3
§18).
"""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.song import LanguageBrief

SourceType = Literal[
    "ORIGINAL", "ARTIST", "RIGHTS_HOLDER", "LICENSE", "PARTNER", "PUBLIC_DOMAIN", "USER_SUBMITTED"
]


class LyricsVisibilityRead(BaseModel):
    """Vue publique — GET /lyrics/song/{song_id} pour un visiteur non
    autorisé à voir le contenu réel (non-auteur, non-ADMIN, ou statut
    != AUTHORIZED / expiré)."""

    available: bool
    language: LanguageBrief | None = None
    content: str | None = None


class LyricsOwnerRead(BaseModel):
    """Vue enrichie — auteur de la soumission ou ADMIN uniquement."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    song_id: UUID
    language: LanguageBrief
    content: str
    source_type: str
    source_url: str | None = None
    rights_holder: str | None = None
    authorization_status: str
    authorization_reference: str | None = None
    authorization_date: date | None = None
    expiration_date: date | None = None
    submitted_by_user_id: UUID | None = None
    reviewed_by_user_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class LyricsCreate(BaseModel):
    """Contrat de soumission — `submitted_by_user_id` et
    `authorization_status` sont structurellement absents : le client
    ne peut physiquement pas les fournir."""

    song_id: UUID
    language_id: UUID
    content: str = Field(min_length=1)
    source_type: SourceType
    source_url: str | None = None
    rights_holder: str | None = Field(default=None, max_length=255)


class LyricsUpdate(BaseModel):
    """Édition — auteur (si PENDING) ou ADMIN. Seuls `content`,
    `source_url`, `rights_holder` sont modifiables ; `song_id`,
    `language_id`, `source_type`, `submitted_by_user_id`,
    `authorization_status`, `reviewed_by_user_id` sont structurellement
    absents de ce schéma."""

    content: str | None = Field(default=None, min_length=1)
    source_url: str | None = None
    rights_holder: str | None = Field(default=None, max_length=255)
