"""Endpoints d'authentification — /api/v1/auth.

Le JWT n'est JAMAIS retourné dans le corps JSON : il est posé
exclusivement via un cookie HttpOnly (présentes instructions Phase 2
§5-6). Ce point diffère du libellé initial du Livrable 3 §2.1 (qui
montrait access_token dans le corps) — écart documenté dans le
rapport de fin de phase, tranché explicitement par les instructions
de cette phase, pas choisi arbitrairement par le service.
"""

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import ACCESS_TOKEN_COOKIE_NAME
from app.core.config import get_settings
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.user import UserPublicRead
from app.services.auth_service import AuthService

router = APIRouter()
settings = get_settings()


def _user_to_public_read(user: User) -> UserPublicRead:
    return UserPublicRead(
        id=user.id,
        email=user.email,
        username=user.username,
        role=user.role.name,
        is_verified=user.is_verified,
        created_at=user.created_at,
    )


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        path="/",
        max_age=settings.jwt_expire_minutes * 60,
    )


@router.post("/register", status_code=201)
async def register(payload: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)) -> dict:
    service = AuthService(db)
    user, token = await service.register(payload)
    _set_auth_cookie(response, token)
    return {"data": _user_to_public_read(user)}


@router.post("/login")
async def login(payload: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)) -> dict:
    service = AuthService(db)
    user, token = await service.login(payload)
    _set_auth_cookie(response, token)
    return {"data": _user_to_public_read(user)}


@router.post("/logout", status_code=204)
async def logout(response: Response) -> None:
    # Idempotent : supprime le cookie qu'il existe ou non.
    response.delete_cookie(key=ACCESS_TOKEN_COOKIE_NAME, path="/")


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)) -> dict:
    return {"data": _user_to_public_read(current_user)}
