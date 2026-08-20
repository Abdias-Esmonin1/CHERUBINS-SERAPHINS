"""Schémas Pydantic pour la ressource User.

UserPublicRead est la SEULE forme de sortie autorisée pour un
utilisateur — jamais le modèle SQLAlchemy sérialisé directement, pour
garantir structurellement qu'aucun champ sensible (password_hash,
deleted_at, ...) ne peut fuiter (Livrable 5 §18, Livrable 2 §13).
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserPublicRead(BaseModel):
    """Contrat exact validé — Livrable 3 §2.4 (GET /auth/me)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    username: str
    role: str
    is_verified: bool
    created_at: datetime
