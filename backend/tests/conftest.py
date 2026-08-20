"""Fixtures partagées pour les tests.

Les variables d'environnement requises par Settings (DATABASE_URL,
JWT_SECRET_KEY) sont injectées ici avec des valeurs de test, avant
tout import de l'application, pour ne dépendre d'aucun fichier .env
réel pendant les tests.

Base de données de test : SQLite en mémoire (aiosqlite), et NON
PostgreSQL. Décision technique de test uniquement (pas une décision
métier) : aucun serveur PostgreSQL n'est disponible dans cet
environnement d'implémentation sandboxé (réseau restreint). La
production/le développement réels restent strictement PostgreSQL
(cf. architecture validée) — ce choix n'affecte que l'exécution des
tests automatisés ici. Un enregistrement de CHAR_LENGTH (fonction SQL
utilisée par une contrainte CHECK Postgres sur `users`) est ajouté à
la connexion SQLite pour permettre la création du schéma sans modifier
les modèles existants.
"""

import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("ENVIRONMENT", "test")

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import get_db
from app.main import app
from app.models import Base, Role


@pytest.fixture
def client() -> TestClient:
    """Client pour les tests Phase 1 qui ne touchent pas la base
    (ex. /health). Les tests nécessitant la base utilisent
    `client_with_db` ci-dessous.
    """
    return TestClient(app)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    @event.listens_for(engine.sync_engine, "connect")
    def _register_sqlite_functions(dbapi_connection, connection_record) -> None:  # noqa: ANN001
        dbapi_connection.create_function("CHAR_LENGTH", 1, len)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_factory() as session:
        # Seed des rôles MVP (USER, ADMIN) — nécessaires à /auth/register.
        session.add_all([Role(name="USER"), Role(name="ADMIN")])
        await session.commit()
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def client_with_db(db_session: AsyncSession) -> AsyncGenerator[TestClient, None]:
    """Client FastAPI avec la dépendance get_db substituée par la
    session SQLite en mémoire de test.
    """

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)
