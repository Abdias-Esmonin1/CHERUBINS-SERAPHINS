from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LanguageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    native_name: str | None = None
    is_active: bool


class LanguageCreate(BaseModel):
    code: str = Field(min_length=2, max_length=10)
    name: str = Field(min_length=1, max_length=100)
    native_name: str | None = None


class LanguageUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    native_name: str | None = None
    is_active: bool | None = None
