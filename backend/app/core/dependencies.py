"""Dépendances FastAPI partagées."""

from dataclasses import dataclass

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import ACCESS_TOKEN_COOKIE_NAME
from app.exceptions import ForbiddenError, UnauthorizedError
from app.models.user import User
from app.services.auth_service import AuthService


@dataclass
class Pagination:
    page: int = 1
    page_size: int = 20


def get_pagination(page: int = 1, page_size: int = 20) -> Pagination:
    """Normalise les paramètres de pagination (convention Livrable 3 §13)."""
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    return Pagination(page=page, page_size=page_size)


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """Résout l'utilisateur courant à partir du JWT porté par le cookie
    HttpOnly. Lève UnauthorizedError (401) si absent/invalide/expiré,
    ou si l'utilisateur n'existe plus / est désactivé / soft-deleted.
    """
    token = request.cookies.get(ACCESS_TOKEN_COOKIE_NAME)
    service = AuthService(db)
    return await service.get_current_user_from_token(token)


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Exige le rôle ADMIN. Le rôle vient exclusivement de la base via
    current_user.role.name — jamais d'une donnée fournie par le client.
    """
    if current_user.role.name != "ADMIN":
        raise ForbiddenError("Accès réservé aux administrateurs.", code="FORBIDDEN")
    return current_user


async def get_current_user_optional(request: Request, db: AsyncSession = Depends(get_db)) -> User | None:
    """Comme get_current_user, mais retourne None au lieu de lever 401
    si aucune session valide n'est présente. Nécessaire pour les
    endpoints publics dont la réponse varie selon que l'appelant est
    anonyme, auteur d'une ressource, ou ADMIN (ex. GET
    /lyrics/song/{id}, Phase 4) sans pour autant exiger
    l'authentification.
    """
    token = request.cookies.get(ACCESS_TOKEN_COOKIE_NAME)
    if token is None:
        return None
    service = AuthService(db)
    try:
        return await service.get_current_user_from_token(token)
    except UnauthorizedError:
        # Token présent mais invalide/expiré/utilisateur introuvable :
        # traité comme anonyme plutôt que de lever une erreur, puisque
        # cet endpoint reste accessible sans authentification.
        return None
