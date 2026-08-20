"""Fixtures partagées pour les tests Phase 1.

Les variables d'environnement requises par Settings (DATABASE_URL,
JWT_SECRET_KEY) sont injectées ici avec des valeurs de test, avant
tout import de l'application, pour ne dépendre d'aucun fichier .env
réel pendant les tests.
"""

import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("ENVIRONMENT", "test")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
