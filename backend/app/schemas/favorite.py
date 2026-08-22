"""Schémas Pydantic pour Favorite.

Ressource strictement privée à `current_user` — pas de vue publique,
pas de notion d'auteur distinct (le propriétaire EST l'utilisateur
connecté), contrairement à Lyrics/Translation.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.song import SongRead


class FavoriteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    song: SongRead
    created_at: datetime


class FavoriteCreate(BaseModel):
    """Contrat de création — `user_id` structurellement absent : jamais
    fourni par le client, toujours `current_user.id` (protection IDOR
    par construction, même principe que /lyrics/mine)."""

    song_id: UUID
