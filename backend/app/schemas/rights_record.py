"""Schémas Pydantic pour RightsRecord et les actions de modération.

RightsRecordRead est la seule forme de sortie — pas de schéma
Create/Update : la table n'est jamais alimentée directement par un
endpoint, uniquement en interne par `moderation_service.py`.
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RightsRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lyrics_id: UUID | None = None
    translation_id: UUID | None = None
    action: str
    previous_status: str | None = None
    new_status: str
    reason: str | None = None
    performed_by_user_id: UUID | None = None
    created_at: datetime


class ModerationAuthorizeRequest(BaseModel):
    """Body pour PATCH .../authorize — lyrics ET translations."""

    authorization_reference: str | None = Field(default=None, max_length=100)
    authorization_date: date | None = None
    expiration_date: date | None = None


class ModerationReasonRequest(BaseModel):
    """Body pour PATCH .../reject et PATCH .../revoke — reason obligatoire."""

    reason: str = Field(min_length=1)
