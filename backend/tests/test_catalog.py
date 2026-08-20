"""Tests Phase 3 — Catalogue (categories, languages, artists, albums, songs)."""

import asyncio

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Artist, Category, Language, Role, User
from app.core.security import hash_password


async def _promote_to_admin(db_session: AsyncSession, email: str) -> None:
    from sqlalchemy import select

    result = await db_session.execute(select(Role).where(Role.name == "ADMIN"))
    admin_role = result.scalar_one()
    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalar_one()
    user.role_id = admin_role.id
    await db_session.commit()


def _admin_client(client_with_db: TestClient, db_session: AsyncSession) -> TestClient:
    """Enregistre un utilisateur, le promeut ADMIN en base, puis se
    reconnecte pour obtenir un cookie reflétant le nouveau rôle."""
    payload = {"email": "admin@example.com", "username": "admin1", "password": "AdminPass123"}
    client_with_db.post("/api/v1/auth/register", json=payload)
    asyncio.get_event_loop().run_until_complete(_promote_to_admin(db_session, payload["email"]))
    client_with_db.cookies.clear()
    client_with_db.post("/api/v1/auth/login", json={"email": payload["email"], "password": payload["password"]})
    return client_with_db


async def _seed_language_and_category(db_session: AsyncSession) -> tuple[str, str]:
    language = Language(code="en", name="English")
    category = Category(name="Louange")
    db_session.add_all([language, category])
    await db_session.commit()
    await db_session.refresh(language)
    await db_session.refresh(category)
    return str(language.id), str(category.id)


def _seed(db_session: AsyncSession) -> tuple[str, str]:
    return asyncio.get_event_loop().run_until_complete(_seed_language_and_category(db_session))


# --------------------------------------------------------- CATEGORIES/LANGUAGES


def test_list_categories_public(client_with_db: TestClient, db_session: AsyncSession) -> None:
    _seed(db_session)
    response = client_with_db.get("/api/v1/categories")
    assert response.status_code == 200
    assert len(response.json()["data"]) == 1
    assert response.json()["data"][0]["name"] == "Louange"


def test_list_languages_public(client_with_db: TestClient, db_session: AsyncSession) -> None:
    _seed(db_session)
    response = client_with_db.get("/api/v1/languages")
    assert response.status_code == 200
    assert response.json()["data"][0]["code"] == "en"


# ----------------------------------------------------------------------- ARTISTS


def test_create_artist_requires_admin(client_with_db: TestClient) -> None:
    payload = {"name": "Sinach"}
    response = client_with_db.post("/api/v1/artists", json=payload)
    assert response.status_code == 401  # non authentifié


def test_create_artist_forbidden_for_non_admin(client_with_db: TestClient) -> None:
    client_with_db.post(
        "/api/v1/auth/register", json={"email": "u@example.com", "username": "user1", "password": "Password123"}
    )
    response = client_with_db.post("/api/v1/artists", json={"name": "Sinach"})
    assert response.status_code == 403


def test_create_artist_as_admin_generates_slug(client_with_db: TestClient, db_session: AsyncSession) -> None:
    admin = _admin_client(client_with_db, db_session)
    response = admin.post("/api/v1/artists", json={"name": "Way Maker Sinach"})
    assert response.status_code == 201
    body = response.json()["data"]
    assert body["slug"] == "way-maker-sinach"
    assert body["name"] == "Way Maker Sinach"


def test_create_artist_duplicate_name_gets_unique_slug(client_with_db: TestClient, db_session: AsyncSession) -> None:
    admin = _admin_client(client_with_db, db_session)
    first = admin.post("/api/v1/artists", json={"name": "Sinach"})
    second = admin.post("/api/v1/artists", json={"name": "Sinach"})
    assert first.json()["data"]["slug"] == "sinach"
    assert second.json()["data"]["slug"] == "sinach-2"


def test_get_artist_by_slug(client_with_db: TestClient, db_session: AsyncSession) -> None:
    admin = _admin_client(client_with_db, db_session)
    admin.post("/api/v1/artists", json={"name": "Sinach"})
    response = client_with_db.get("/api/v1/artists/sinach")
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Sinach"


def test_get_artist_unknown_slug_returns_404(client_with_db: TestClient) -> None:
    response = client_with_db.get("/api/v1/artists/unknown-artist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ARTIST_NOT_FOUND"


def test_list_artists_paginated(client_with_db: TestClient, db_session: AsyncSession) -> None:
    admin = _admin_client(client_with_db, db_session)
    for name in ("Sinach", "CeCe Winans", "Dena Mwana"):
        admin.post("/api/v1/artists", json={"name": name})
    response = client_with_db.get("/api/v1/artists?page=1&page_size=2")
    body = response.json()
    assert len(body["data"]) == 2
    assert body["meta"]["total"] == 3
    assert body["meta"]["total_pages"] == 2


def test_artist_create_client_cannot_set_slug(client_with_db: TestClient, db_session: AsyncSession) -> None:
    """Le schéma ArtistCreate n'accepte pas `slug` — conforme Livrable 3 §4.3."""
    admin = _admin_client(client_with_db, db_session)
    response = admin.post("/api/v1/artists", json={"name": "Test Artist", "slug": "hacked-slug"})
    assert response.status_code == 201
    assert response.json()["data"]["slug"] == "test-artist"


# ------------------------------------------------------------------------ ALBUMS


def test_create_album_requires_existing_artist(client_with_db: TestClient, db_session: AsyncSession) -> None:
    admin = _admin_client(client_with_db, db_session)
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = admin.post("/api/v1/albums", json={"artist_id": fake_id, "title": "Some Album"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ARTIST_NOT_FOUND"


def test_create_and_get_album(client_with_db: TestClient, db_session: AsyncSession) -> None:
    admin = _admin_client(client_with_db, db_session)
    artist_resp = admin.post("/api/v1/artists", json={"name": "Sinach"})
    artist_id = artist_resp.json()["data"]["id"]

    album_resp = admin.post("/api/v1/albums", json={"artist_id": artist_id, "title": "Way Maker"})
    assert album_resp.status_code == 201
    album_id = album_resp.json()["data"]["id"]

    get_resp = client_with_db.get(f"/api/v1/albums/{album_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["title"] == "Way Maker"


def test_list_albums_filtered_by_artist(client_with_db: TestClient, db_session: AsyncSession) -> None:
    admin = _admin_client(client_with_db, db_session)
    a1 = admin.post("/api/v1/artists", json={"name": "Artist One"}).json()["data"]["id"]
    a2 = admin.post("/api/v1/artists", json={"name": "Artist Two"}).json()["data"]["id"]
    admin.post("/api/v1/albums", json={"artist_id": a1, "title": "Album A"})
    admin.post("/api/v1/albums", json={"artist_id": a2, "title": "Album B"})

    response = client_with_db.get(f"/api/v1/albums?artist_id={a1}")
    assert len(response.json()["data"]) == 1
    assert response.json()["data"][0]["title"] == "Album A"


# ------------------------------------------------------------------------- SONGS


def test_create_song_defaults_to_draft_and_not_publicly_visible(
    client_with_db: TestClient, db_session: AsyncSession
) -> None:
    language_id, category_id = _seed(db_session)
    admin = _admin_client(client_with_db, db_session)
    artist_id = admin.post("/api/v1/artists", json={"name": "Sinach"}).json()["data"]["id"]

    create_resp = admin.post(
        "/api/v1/songs",
        json={
            "title": "Way Maker",
            "artist_id": artist_id,
            "category_id": category_id,
            "original_language_id": language_id,
        },
    )
    assert create_resp.status_code == 201
    assert create_resp.json()["data"]["status"] == "DRAFT"
    slug = create_resp.json()["data"]["slug"]

    # Une chanson DRAFT n'est pas visible publiquement (liste ni détail).
    public_get = client_with_db.get(f"/api/v1/songs/{slug}")
    assert public_get.status_code == 404

    public_list = client_with_db.get("/api/v1/songs")
    assert public_list.json()["meta"]["total"] == 0


def test_publish_song_makes_it_publicly_visible(client_with_db: TestClient, db_session: AsyncSession) -> None:
    language_id, category_id = _seed(db_session)
    admin = _admin_client(client_with_db, db_session)
    artist_id = admin.post("/api/v1/artists", json={"name": "Sinach"}).json()["data"]["id"]
    song = admin.post(
        "/api/v1/songs",
        json={
            "title": "Way Maker",
            "artist_id": artist_id,
            "category_id": category_id,
            "original_language_id": language_id,
        },
    ).json()["data"]

    update_resp = admin.put(f"/api/v1/songs/{song['id']}", json={"status": "PUBLISHED"})
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["status"] == "PUBLISHED"

    public_get = client_with_db.get(f"/api/v1/songs/{song['slug']}")
    assert public_get.status_code == 200
    assert public_get.json()["data"]["artist"]["name"] == "Sinach"
    assert public_get.json()["data"]["original_language"]["code"] == "en"


def test_search_songs_by_title(client_with_db: TestClient, db_session: AsyncSession) -> None:
    language_id, category_id = _seed(db_session)
    admin = _admin_client(client_with_db, db_session)
    artist_id = admin.post("/api/v1/artists", json={"name": "Sinach"}).json()["data"]["id"]
    song = admin.post(
        "/api/v1/songs",
        json={
            "title": "Way Maker",
            "artist_id": artist_id,
            "category_id": category_id,
            "original_language_id": language_id,
        },
    ).json()["data"]
    admin.put(f"/api/v1/songs/{song['id']}", json={"status": "PUBLISHED"})

    response = client_with_db.get("/api/v1/songs/search?q=way")
    assert response.status_code == 200
    assert response.json()["meta"]["total"] == 1
    assert response.json()["data"][0]["title"] == "Way Maker"


def test_search_songs_by_artist_name(client_with_db: TestClient, db_session: AsyncSession) -> None:
    language_id, category_id = _seed(db_session)
    admin = _admin_client(client_with_db, db_session)
    artist_id = admin.post("/api/v1/artists", json={"name": "Sinach"}).json()["data"]["id"]
    song = admin.post(
        "/api/v1/songs",
        json={
            "title": "Way Maker",
            "artist_id": artist_id,
            "category_id": category_id,
            "original_language_id": language_id,
        },
    ).json()["data"]
    admin.put(f"/api/v1/songs/{song['id']}", json={"status": "PUBLISHED"})

    response = client_with_db.get("/api/v1/songs/search?q=sinach")
    assert response.json()["meta"]["total"] == 1


def test_search_songs_missing_query_returns_422(client_with_db: TestClient) -> None:
    response = client_with_db.get("/api/v1/songs/search")
    assert response.status_code == 422


def test_search_songs_no_result(client_with_db: TestClient, db_session: AsyncSession) -> None:
    _seed(db_session)
    response = client_with_db.get("/api/v1/songs/search?q=nonexistent")
    assert response.status_code == 200
    assert response.json()["meta"]["total"] == 0
    assert response.json()["data"] == []


def test_create_song_unknown_artist_returns_404(client_with_db: TestClient, db_session: AsyncSession) -> None:
    language_id, category_id = _seed(db_session)
    admin = _admin_client(client_with_db, db_session)
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = admin.post(
        "/api/v1/songs",
        json={
            "title": "Way Maker",
            "artist_id": fake_id,
            "category_id": category_id,
            "original_language_id": language_id,
        },
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ARTIST_NOT_FOUND"


def test_create_song_unknown_language_returns_404(client_with_db: TestClient, db_session: AsyncSession) -> None:
    admin = _admin_client(client_with_db, db_session)
    artist_id = admin.post("/api/v1/artists", json={"name": "Sinach"}).json()["data"]["id"]
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = admin.post(
        "/api/v1/songs", json={"title": "Way Maker", "artist_id": artist_id, "original_language_id": fake_id}
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "LANGUAGE_NOT_FOUND"


def test_create_song_forbidden_for_non_admin(client_with_db: TestClient, db_session: AsyncSession) -> None:
    language_id, category_id = _seed(db_session)
    client_with_db.post(
        "/api/v1/auth/register", json={"email": "u2@example.com", "username": "user2", "password": "Password123"}
    )
    response = client_with_db.post(
        "/api/v1/songs",
        json={
            "title": "Way Maker",
            "artist_id": "00000000-0000-0000-0000-000000000000",
            "category_id": category_id,
            "original_language_id": language_id,
        },
    )
    assert response.status_code == 403


def test_update_song_client_cannot_bypass_admin(client_with_db: TestClient, db_session: AsyncSession) -> None:
    language_id, category_id = _seed(db_session)
    admin = _admin_client(client_with_db, db_session)
    artist_id = admin.post("/api/v1/artists", json={"name": "Sinach"}).json()["data"]["id"]
    song = admin.post(
        "/api/v1/songs",
        json={
            "title": "Way Maker",
            "artist_id": artist_id,
            "category_id": category_id,
            "original_language_id": language_id,
        },
    ).json()["data"]

    client_with_db.cookies.clear()
    client_with_db.post(
        "/api/v1/auth/register", json={"email": "u3@example.com", "username": "user3", "password": "Password123"}
    )
    response = client_with_db.put(f"/api/v1/songs/{song['id']}", json={"status": "PUBLISHED"})
    assert response.status_code == 403


# ------------------------------------------------------------ NON-REGRESSION


def test_health_still_works(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_auth_register_still_works(client_with_db: TestClient) -> None:
    response = client_with_db.post(
        "/api/v1/auth/register",
        json={"email": "regcheck@example.com", "username": "regcheck", "password": "Password123"},
    )
    assert response.status_code == 201
