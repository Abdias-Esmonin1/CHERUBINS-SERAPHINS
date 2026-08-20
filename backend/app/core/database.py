"""Connexion PostgreSQL (SQLAlchemy 2.x, async) et dépendance FastAPI get_db."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Fournit une session SQLAlchemy par requête, fermée automatiquement."""
    async with AsyncSessionLocal() as session:
        yield session
