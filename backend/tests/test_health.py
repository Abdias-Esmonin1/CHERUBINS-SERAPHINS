"""Tests Phase 1 : import de l'application et endpoint /health."""

from fastapi.testclient import TestClient


def test_app_imports_without_error() -> None:
    """L'application FastAPI doit pouvoir être importée sans lever d'exception."""
    from app.main import app

    assert app is not None


def test_health_endpoint_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "environment" in body


def test_health_endpoint_is_not_versioned(client: TestClient) -> None:
    """/health doit rester hors du préfixe /api/v1 (Livrable 3 §12)."""
    response = client.get("/api/v1/health")
    assert response.status_code == 404
