"""Tests Phase 6 — Favorites (ajout, suppression, liste).

Favorite n'a aucune notion de droits/statut — ressource strictement
privée à current_user. Décision documentée (§14 du plan validé) :
aucune restriction sur Song.status, vérifiée explicitement par un test
dédié.
"""

import asyncio
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Artist, Category, Language, Song

# ------------------------------------------------------------------- HELPERS


async def _seed_song(db_session: AsyncSession, status: str = "PUBLISHED", slug: str = "way-maker") -> str:
    from sqlalchemy import select

    result = await db_session.execute(select(Language).where(Language.code == "en"))
    language = result.scalar_one_or_none()
    if language is None:
        language = Language(code="en", name="English")
        db_session.add(language)
        await db_session.flush()

    result = await db_session.execute(select(Category).where(Category.name == "Louange"))
    category = result.scalar_one_or_none()
    if category is None:
        category = Category(name="Louange")
        db_session.add(category)
        await db_session.flush()

    artist = Artist(name="Sinach", slug=f"sinach-{slug}")
    db_session.add(artist)
    await db_session.flush()

    song = Song(
        title="Way Maker",
        slug=slug,
        artist_id=artist.id,
        category_id=category.id,
        original_language_id=language.id,
        status=status,
    )
    db_session.add(song)
    await db_session.commit()
    await db_session.refresh(song)
    return str(song.id)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def _seed(db_session: AsyncSession, status: str = "PUBLISHED", slug: str = "way-maker") -> str:
    return _run(_seed_song(db_session, status=status, slug=slug))


def _register(client_with_db: TestClient, email: str, username: str, password: str = "Password123") -> None:
    client_with_db.cookies.clear()
    client_with_db.post("/api/v1/auth/register", json={"email": email, "username": username, "password": password})


# --------------------------------------------------------------------- ADD


def test_add_favorite_valid(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id = _seed(db_session)
    _register(client_with_db, "fav1@example.com", "favuser1")
    response = client_with_db.post("/api/v1/favorites", json={"song_id": song_id})
    assert response.status_code == 201
    body = response.json()["data"]
    assert body["song"]["id"] == song_id
    assert "id" in body and "created_at" in body


def test_add_favorite_requires_auth(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id = _seed(db_session)
    response = client_with_db.post("/api/v1/favorites", json={"song_id": song_id})
    assert response.status_code == 401


def test_add_favorite_unknown_song_returns_404(client_with_db: TestClient, db_session: AsyncSession) -> None:
    _register(client_with_db, "fav2@example.com", "favuser2")
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client_with_db.post("/api/v1/favorites", json={"song_id": fake_id})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SONG_NOT_FOUND"


def test_add_favorite_duplicate_returns_409(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id = _seed(db_session)
    _register(client_with_db, "fav3@example.com", "favuser3")
    client_with_db.post("/api/v1/favorites", json={"song_id": song_id})
    response = client_with_db.post("/api/v1/favorites", json={"song_id": song_id})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "ALREADY_FAVORITED"


def test_add_favorite_draft_song_is_allowed(client_with_db: TestClient, db_session: AsyncSession) -> None:
    """Décision Phase 6 documentée : aucune restriction sur Song.status
    — seule l'existence de la chanson est vérifiée."""
    song_id = _seed(db_session, status="DRAFT", slug="draft-song")
    _register(client_with_db, "fav4@example.com", "favuser4")
    response = client_with_db.post("/api/v1/favorites", json={"song_id": song_id})
    assert response.status_code == 201


def test_add_favorite_client_cannot_set_user_id(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id = _seed(db_session)
    _register(client_with_db, "fav5@example.com", "favuser5")
    fake_user_id = "11111111-1111-1111-1111-111111111111"
    response = client_with_db.post("/api/v1/favorites", json={"song_id": song_id, "user_id": fake_user_id})
    assert response.status_code == 201  # user_id absent du schéma, silencieusement ignoré


# -------------------------------------------------------------------- LIST


def test_list_favorites_scoped_to_current_user(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id = _seed(db_session)
    _register(client_with_db, "fav6@example.com", "favuser6")
    client_with_db.post("/api/v1/favorites", json={"song_id": song_id})

    _register(client_with_db, "fav7@example.com", "favuser7")
    response = client_with_db.get("/api/v1/favorites")
    assert response.status_code == 200
    assert response.json()["data"] == []
    assert response.json()["meta"]["total"] == 0


def test_list_favorites_empty(client_with_db: TestClient) -> None:
    _register(client_with_db, "fav8@example.com", "favuser8")
    response = client_with_db.get("/api/v1/favorites")
    assert response.status_code == 200
    assert response.json()["data"] == []


def test_list_favorites_requires_auth(client_with_db: TestClient) -> None:
    response = client_with_db.get("/api/v1/favorites")
    assert response.status_code == 401


def test_list_favorites_includes_song_details(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id = _seed(db_session)
    _register(client_with_db, "fav9@example.com", "favuser9")
    client_with_db.post("/api/v1/favorites", json={"song_id": song_id})
    response = client_with_db.get("/api/v1/favorites")
    body = response.json()["data"][0]
    assert body["song"]["title"] == "Way Maker"
    assert body["song"]["artist"]["name"] == "Sinach"


def test_list_favorites_pagination(client_with_db: TestClient, db_session: AsyncSession) -> None:
    _register(client_with_db, "fav10@example.com", "favuser10")
    for i in range(3):
        song_id = _seed(db_session, slug=f"song-pagination-{i}")
        client_with_db.post("/api/v1/favorites", json={"song_id": song_id})

    response = client_with_db.get("/api/v1/favorites?page=1&page_size=2")
    body = response.json()
    assert len(body["data"]) == 2
    assert body["meta"]["total"] == 3
    assert body["meta"]["total_pages"] == 2


# ------------------------------------------------------------------ REMOVE


def test_remove_favorite_valid(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id = _seed(db_session)
    _register(client_with_db, "fav11@example.com", "favuser11")
    client_with_db.post("/api/v1/favorites", json={"song_id": song_id})

    response = client_with_db.delete(f"/api/v1/favorites/{song_id}")
    assert response.status_code == 204

    list_response = client_with_db.get("/api/v1/favorites")
    assert list_response.json()["meta"]["total"] == 0


def test_remove_favorite_unknown_returns_404(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id = _seed(db_session)
    _register(client_with_db, "fav12@example.com", "favuser12")
    response = client_with_db.delete(f"/api/v1/favorites/{song_id}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "FAVORITE_NOT_FOUND"


def test_remove_favorite_cannot_remove_another_users_favorite(client_with_db: TestClient, db_session: AsyncSession) -> None:
    """IDOR : un utilisateur ne peut pas supprimer le favori d'un autre,
    même en connaissant le song_id — la suppression échoue avec
    FAVORITE_NOT_FOUND (pas d'énumération de ce que possède autrui)."""
    song_id = _seed(db_session)
    _register(client_with_db, "fav13@example.com", "favuser13")
    client_with_db.post("/api/v1/favorites", json={"song_id": song_id})

    _register(client_with_db, "fav14@example.com", "favuser14")
    response = client_with_db.delete(f"/api/v1/favorites/{song_id}")
    assert response.status_code == 404

    client_with_db.cookies.clear()
    client_with_db.post("/api/v1/auth/login", json={"email": "fav13@example.com", "password": "Password123"})
    still_there = client_with_db.get("/api/v1/favorites")
    assert still_there.json()["meta"]["total"] == 1


def test_remove_favorite_requires_auth(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id = _seed(db_session)
    response = client_with_db.delete(f"/api/v1/favorites/{song_id}")
    assert response.status_code == 401


# --------------------------------------------------------------- SECURITY


def test_favorites_responses_never_leak_password_or_hash(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id = _seed(db_session)
    _register(client_with_db, "favsec@example.com", "favsecuser", password="SuperSecretPass3")
    r1 = client_with_db.post("/api/v1/favorites", json={"song_id": song_id})
    r2 = client_with_db.get("/api/v1/favorites")
    for response in (r1, r2):
        assert "SuperSecretPass3" not in response.text
        assert "password_hash" not in response.text


# ------------------------------------------------------------ NON-REGRESSION


def test_health_still_works(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_catalog_still_works(client_with_db: TestClient, db_session: AsyncSession) -> None:
    _seed(db_session)
    response = client_with_db.get("/api/v1/songs")
    assert response.status_code == 200
    assert response.json()["meta"]["total"] == 1


def test_auth_still_works(client_with_db: TestClient) -> None:
    response = client_with_db.post(
        "/api/v1/auth/register",
        json={"email": "favregcheck@example.com", "username": "favregcheck", "password": "Password123"},
    )
    assert response.status_code == 201


def test_lyrics_still_works(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id = _seed(db_session)
    _register(client_with_db, "favlyricscheck@example.com", "favlyricscheck")

    async def _get_language_id() -> str:
        from sqlalchemy import select

        result = await db_session.execute(select(Language).where(Language.code == "en"))
        return str(result.scalar_one().id)

    language_id = _run(_get_language_id())
    response = client_with_db.post(
        "/api/v1/lyrics",
        json={"song_id": song_id, "language_id": language_id, "content": "x", "source_type": "ORIGINAL"},
    )
    assert response.status_code == 201


def test_translations_still_works(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id = _seed(db_session)
    _register(client_with_db, "favtransl@example.com", "favtransl")

    async def _setup() -> tuple[str, str]:
        from sqlalchemy import select

        from app.models import Lyrics, User

        result = await db_session.execute(select(Language).where(Language.code == "en"))
        lang = result.scalar_one()
        target = Language(code="fr", name="Français")
        db_session.add(target)
        await db_session.flush()
        user_result = await db_session.execute(select(User).where(User.email == "favtransl@example.com"))
        user = user_result.scalar_one()
        lyrics = Lyrics(
            song_id=UUID(song_id),
            language_id=lang.id,
            content="x",
            source_type="ORIGINAL",
            submitted_by_user_id=user.id,
        )
        db_session.add(lyrics)
        await db_session.commit()
        await db_session.refresh(lyrics)
        await db_session.refresh(target)
        return str(lyrics.id), str(target.id)

    lyrics_id, target_language_id = _run(_setup())
    response = client_with_db.post(
        "/api/v1/translations",
        json={
            "lyrics_id": lyrics_id,
            "target_language_id": target_language_id,
            "content": "x",
            "translation_type": "HUMAN",
        },
    )
    assert response.status_code == 201
