"""Schémas Pydantic pour l'authentification.

Ces schémas d'entrée n'incluent structurellement aucun champ interne
(role, password_hash, is_verified, deleted_at, ...) — le client ne
peut donc physiquement pas les fournir, conformément à la règle
validée (Livrable 3 §15, présentes instructions §4).
"""

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def username_no_whitespace(cls, value: str) -> str:
        if value != value.strip() or " " in value:
            raise ValueError("Le nom d'utilisateur ne doit pas contenir d'espaces.")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)
