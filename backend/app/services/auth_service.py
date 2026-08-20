"""Service d'authentification — logique métier, aucune réponse HTTP construite ici.

Cf. Livrable 2 §2.1 : un service ne lève que des exceptions métier
(app.exceptions), jamais de HTTPException.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.exceptions import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError
from app.models.user import User
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest

# Message générique volontairement identique pour "email inconnu" et
# "mot de passe incorrect" — anti-énumération de comptes
# (Livrable 3 §2.2, décision validée).
_INVALID_CREDENTIALS_MESSAGE = "Email ou mot de passe incorrect."


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._users = UserRepository(session)
        self._roles = RoleRepository(session)

    async def register(self, payload: RegisterRequest) -> tuple[User, str]:
        if await self._users.get_by_email(payload.email) is not None:
            raise ConflictError("Cette adresse email est déjà utilisée.", code="EMAIL_ALREADY_EXISTS")
        if await self._users.get_by_username(payload.username) is not None:
            raise ConflictError("Ce nom d'utilisateur est déjà utilisé.", code="USERNAME_ALREADY_EXISTS")

        default_role = await self._roles.get_by_name("USER")
        if default_role is None:
            # Erreur de configuration serveur (seed des rôles manquant),
            # pas une erreur utilisateur — ne doit normalement jamais
            # se produire si la base a été correctement initialisée.
            raise NotFoundError("Rôle par défaut introuvable.", code="DEFAULT_ROLE_MISSING")

        user = User(
            role_id=default_role.id,
            email=payload.email,
            username=payload.username,
            password_hash=hash_password(payload.password),
        )
        user = await self._users.create(user)
        await self._session.commit()
        await self._session.refresh(user, attribute_names=["role"])

        token = create_access_token(subject=str(user.id))
        return user, token

    async def login(self, payload: LoginRequest) -> tuple[User, str]:
        user = await self._users.get_by_email(payload.email)
        if user is None or user.deleted_at is not None:
            raise UnauthorizedError(_INVALID_CREDENTIALS_MESSAGE, code="INVALID_CREDENTIALS")
        if not verify_password(payload.password, user.password_hash):
            raise UnauthorizedError(_INVALID_CREDENTIALS_MESSAGE, code="INVALID_CREDENTIALS")
        if not user.is_active:
            raise ForbiddenError("Votre compte est désactivé.", code="ACCOUNT_DISABLED")

        user.last_login_at = datetime.now(UTC)
        await self._session.commit()
        await self._session.refresh(user, attribute_names=["role"])

        token = create_access_token(subject=str(user.id))
        return user, token

    async def get_current_user_from_token(self, token: str | None) -> User:
        if token is None:
            raise UnauthorizedError("Authentification requise.", code="UNAUTHORIZED")

        payload = decode_access_token(token)
        if payload is None or "sub" not in payload:
            raise UnauthorizedError("Session invalide ou expirée.", code="UNAUTHORIZED")

        try:
            user_id = UUID(payload["sub"])
        except ValueError as exc:
            raise UnauthorizedError("Session invalide ou expirée.", code="UNAUTHORIZED") from exc

        user = await self._users.get_by_id(user_id)
        if user is None or user.deleted_at is not None or not user.is_active:
            raise UnauthorizedError("Session invalide ou expirée.", code="UNAUTHORIZED")

        await self._session.refresh(user, attribute_names=["role"])
        return user
