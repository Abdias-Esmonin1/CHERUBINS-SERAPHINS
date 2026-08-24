"""Schémas Pydantic pour Translation.

Mêmes principes que Lyrics (Livrable 3 §18) : séparation structurelle
entre vue publique et vue enrichie auteur/ADMIN.

GET /translations/lyrics/{lyrics_id} retourne une LISTE (une entrée
par langue cible ayant une traduction soumise), car plusieurs
traductions indépendantes — avec des auteurs et statuts potentiellement
différents — peuvent exister pour une même parole originale.
"""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.song import LanguageBrief

TranslationType = Literal["OFFICIAL", "AUTHOR", "HUMAN", "AI_GENERATED"]


class TranslationVisibilityItem(BaseModel):
    """Élément de la liste publique — une langue cible.

    `translation_type` et `content` restent absents (None) lorsque
    `available = False`, pour ne rien révéler d'une traduction non
    visible (même principe que pour les paroles)."""

    available: bool
    target_language: LanguageBrief
    translation_type: str | None = None
    content: str | None = None


class TranslationOwnerRead(BaseModel):
    """Vue enrichie — auteur de la soumission ou ADMIN uniquement."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lyrics_id: UUID
    target_language: LanguageBrief
    content: str
    translation_type: str
    authorization_status: str
    authorization_reference: str | None = None
    authorization_date: date | None = None
    expiration_date: date | None = None
    source_url: str | None = None
    rights_holder: str | None = None
    submitted_by_user_id: UUID | None = None
    reviewed_by_user_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class TranslationCreate(BaseModel):
    """Contrat de soumission — `submitted_by_user_id` et
    `authorization_status` structurellement absents. La soumission est
    autorisée même si les paroles originales ne sont pas encore
    `AUTHORIZED` (décision validée en conception)."""

    lyrics_id: UUID
    target_language_id: UUID
    content: str = Field(min_length=1)
    translation_type: TranslationType
    source_url: str | None = None
    rights_holder: str | None = Field(default=None, max_length=255)


class TranslationUpdate(BaseModel):
    """Édition — auteur (si PENDING) ou ADMIN, même restriction que
    pour Lyrics. Seuls `content`, `source_url`, `rights_holder`
    modifiables."""

    content: str | None = Field(default=None, min_length=1)
    source_url: str | None = None
    rights_holder: str | None = Field(default=None, max_length=255)
