"""Repository Role — accès données pur.

Minimal en Phase 2 : uniquement la résolution du rôle par défaut
(USER) nécessaire à l'inscription. Pas de CRUD complet ici (hors
périmètre de cette phase).
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Role


class RoleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_name(self, name: str) -> Role | None:
        result = await self._session.execute(select(Role).where(Role.name == name))
        return result.scalar_one_or_none()
