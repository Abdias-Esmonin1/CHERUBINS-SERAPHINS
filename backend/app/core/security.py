"""Utilitaires de sécurité : hash des mots de passe et JWT.

Ce module ne contient que les fonctions bas niveau. Les endpoints
d'authentification (register/login/logout/me) sont implémentés en
Phase 2, conformément à l'ordre d'implémentation validé.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Nom du cookie HttpOnly portant le JWT (Livrable 2 §13, présentes
# instructions §5-6 Phase 2). Jamais accessible en JavaScript.
ACCESS_TOKEN_COOKIE_NAME = "access_token"


def hash_password(password: str) -> str:
    """Hash un mot de passe en clair avec bcrypt."""
    return _pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Vérifie un mot de passe en clair contre son hash bcrypt."""
    return _pwd_context.verify(plain_password, password_hash)


def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    """Crée un JWT d'accès courte durée (pas de refresh token en MVP,
    décision validée — Livrable 2 §13, confirmée Livrable 3).
    """
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    to_encode: dict[str, Any] = {"sub": subject, "exp": expire}
    if extra_claims:
        to_encode.update(extra_claims)
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Décode et valide un JWT. Retourne None si invalide ou expiré."""
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
