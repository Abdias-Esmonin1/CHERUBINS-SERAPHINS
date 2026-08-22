"""Tests Phase 4 — Lyrics (soumission, visibilité, édition, /mine).

Conformément à la validation Option A : aucune transition de statut
n'est possible via l'API dans cette phase (pas d'endpoint
authorize/reject/revoke — Phase 7). Les tests de visibilité
AUTHORIZED/EXPIRED manipulent donc directement l'état en base, comme
explicitement autorisé.
"""

import asyncio
from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Artist, Category, Language, Lyrics, Role, Song, User

# ------------------------------------------------------------------- HELPERS


async def _promote_to_admin(db_session: AsyncSession, email: str) -> None:
    result = await db_session.execute(select(Role).where(Role.name == "ADMIN"))
    admin_role = result.scalar_one()
    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalar_one()
    user.role_id = admin_role.id
    await db_session.commit()


def _admin_client(client_with_db: TestClient, db_session: AsyncSession, suffix: str = "") -> TestClient:
    payload = {
        "email": f"admin{suffix}@example.com",
        "username": f"admin{suffix or '1'}",
        "password": "AdminPass123",
    }
    client_with_db.post("/api/v1/auth/register", json=payload)
    asyncio.get_event_loop().run_until_complete(_promote_to_admin(db_session, payload["email"]))
    client_with_db.cookies.clear()
    client_with_db.post("/api/v1/auth/login", json={"email": payload["email"], "password": payload["password"]})
    return client_with_db


async def _seed_and_publish_song(db_session: AsyncSession) -> tuple[str, str]:
    """Crée langue/catégorie/artiste/chanson PUBLISHED directement en
    base (plus rapide et plus simple que de repasser par l'API admin
    pour chaque test). Retourne (song_id, language_id) en str."""
    language = Language(code="en", name="English")
    category = Category(name="Louange")
    db_session.add_all([language, category])
    await db_session.flush()

    artist = Artist(name="Sinach", slug="sinach")
    db_session.add(artist)
    await db_session.flush()

    song = Song(
        title="Way Maker",
        slug="way-maker",
        artist_id=artist.id,
        category_id=category.id,
        original_language_id=language.id,
        status="PUBLISHED",
    )
    db_session.add(song)
    await db_session.commit()
    await db_session.refresh(song)
    await db_session.refresh(language)
    return str(song.id), str(language.id)


def _seed(db_session: AsyncSession) -> tuple[str, str]:
    return asyncio.get_event_loop().run_until_complete(_seed_and_publish_song(db_session))


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


async def _set_lyrics_field(db_session: AsyncSession, lyrics_id: str, **fields) -> None:
    from uuid import UUID

    result = await db_session.execute(select(Lyrics).where(Lyrics.id == UUID(lyrics_id)))
    lyrics = result.scalar_one()
    for key, value in fields.items():
        setattr(lyrics, key, value)
    await db_session.commit()


def _register(client_with_db: TestClient, email: str, username: str, password: str = "Password123") -> None:
    client_with_db.cookies.clear()
    client_with_db.post("/api/v1/auth/register", json={"email": email, "username": username, "password": password})


def _login(client_with_db: TestClient, email: str, password: str = "Password123") -> None:
    client_with_db.cookies.clear()
    client_with_db.post("/api/v1/auth/login", json={"email": email, "password": password})


# ------------------------------------------------------------------- SUBMIT


def test_submit_lyrics_valid_forces_pending_and_submitter(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, language_id = _seed(db_session)
    _register(client_with_db, "author@example.com", "author1")

    response = client_with_db.post(
        "/api/v1/lyrics",
        json={
            "song_id": song_id,
            "language_id": language_id,
            "content": "You don't need might to be a warrior",
            "source_type": "USER_SUBMITTED",
        },
    )
    assert response.status_code == 201
    body = response.json()["data"]
    assert body["authorization_status"] == "PENDING"
    me = client_with_db.get("/api/v1/auth/me").json()["data"]
    assert body["submitted_by_user_id"] == me["id"]


def test_submit_lyrics_requires_auth(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, language_id = _seed(db_session)
    response = client_with_db.post(
        "/api/v1/lyrics",
        json={"song_id": song_id, "language_id": language_id, "content": "x", "source_type": "ORIGINAL"},
    )
    assert response.status_code == 401


def test_submit_lyrics_unknown_song_returns_404(client_with_db: TestClient, db_session: AsyncSession) -> None:
    _, language_id = _seed(db_session)
    _register(client_with_db, "author2@example.com", "author2")
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client_with_db.post(
        "/api/v1/lyrics",
        json={"song_id": fake_id, "language_id": language_id, "content": "x", "source_type": "ORIGINAL"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SONG_NOT_FOUND"


def test_submit_lyrics_unknown_language_returns_404(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, _ = _seed(db_session)
    _register(client_with_db, "author3@example.com", "author3")
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client_with_db.post(
        "/api/v1/lyrics",
        json={"song_id": song_id, "language_id": fake_id, "content": "x", "source_type": "ORIGINAL"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "LANGUAGE_NOT_FOUND"


def test_submit_lyrics_duplicate_returns_409(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, language_id = _seed(db_session)
    _register(client_with_db, "author4@example.com", "author4")
    payload = {"song_id": song_id, "language_id": language_id, "content": "x", "source_type": "ORIGINAL"}
    client_with_db.post("/api/v1/lyrics", json=payload)
    response = client_with_db.post("/api/v1/lyrics", json=payload)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "LYRICS_ALREADY_EXISTS"


def test_submit_lyrics_invalid_source_type_returns_422(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, language_id = _seed(db_session)
    _register(client_with_db, "author5@example.com", "author5")
    response = client_with_db.post(
        "/api/v1/lyrics",
        json={"song_id": song_id, "language_id": language_id, "content": "x", "source_type": "NOT_A_REAL_TYPE"},
    )
    assert response.status_code == 422


def test_submit_lyrics_client_cannot_set_status_or_submitter(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, language_id = _seed(db_session)
    _register(client_with_db, "author6@example.com", "author6")
    fake_user_id = "11111111-1111-1111-1111-111111111111"
    response = client_with_db.post(
        "/api/v1/lyrics",
        json={
            "song_id": song_id,
            "language_id": language_id,
            "content": "x",
            "source_type": "ORIGINAL",
            "authorization_status": "AUTHORIZED",
            "submitted_by_user_id": fake_user_id,
        },
    )
    assert response.status_code == 201
    body = response.json()["data"]
    assert body["authorization_status"] == "PENDING"
    assert body["submitted_by_user_id"] != fake_user_id


# ---------------------------------------------------------------- VISIBILITY


def test_visibility_no_lyrics_yet_returns_unavailable(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, _ = _seed(db_session)
    response = client_with_db.get(f"/api/v1/lyrics/song/{song_id}")
    assert response.status_code == 200
    assert response.json()["data"] == {"available": False, "language": None, "content": None}


def test_visibility_song_not_found_returns_404(client_with_db: TestClient) -> None:
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client_with_db.get(f"/api/v1/lyrics/song/{fake_id}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SONG_NOT_FOUND"


def test_visibility_pending_hidden_from_public(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, language_id = _seed(db_session)
    _register(client_with_db, "author7@example.com", "author7")
    client_with_db.post(
        "/api/v1/lyrics",
        json={"song_id": song_id, "language_id": language_id, "content": "secret content", "source_type": "ORIGINAL"},
    )
    client_with_db.cookies.clear()  # visiteur anonyme
    response = client_with_db.get(f"/api/v1/lyrics/song/{song_id}")
    assert response.status_code == 200
    assert response.json()["data"]["available"] is False
    assert "content" not in response.text or response.json()["data"]["content"] is None


def test_visibility_authorized_visible_to_public(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, language_id = _seed(db_session)
    _register(client_with_db, "author8@example.com", "author8")
    create_resp = client_with_db.post(
        "/api/v1/lyrics",
        json={"song_id": song_id, "language_id": language_id, "content": "public content", "source_type": "ORIGINAL"},
    )
    lyrics_id = create_resp.json()["data"]["id"]

    # Manipulation directe en base, explicitement autorisée (pas d'endpoint de modération en Phase 4).
    _run(_set_lyrics_field(db_session, lyrics_id, authorization_status="AUTHORIZED"))

    client_with_db.cookies.clear()
    response = client_with_db.get(f"/api/v1/lyrics/song/{song_id}")
    assert response.status_code == 200
    assert response.json()["data"]["available"] is True
    assert response.json()["data"]["content"] == "public content"
    assert response.json()["data"]["language"]["code"] == "en"


def test_visibility_authorized_but_expired_hidden_from_public(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, language_id = _seed(db_session)
    _register(client_with_db, "author9@example.com", "author9")
    create_resp = client_with_db.post(
        "/api/v1/lyrics",
        json={"song_id": song_id, "language_id": language_id, "content": "expired content", "source_type": "ORIGINAL"},
    )
    lyrics_id = create_resp.json()["data"]["id"]

    yesterday = date.today() - timedelta(days=1)
    _run(_set_lyrics_field(db_session, lyrics_id, authorization_status="AUTHORIZED", expiration_date=yesterday))

    client_with_db.cookies.clear()
    response = client_with_db.get(f"/api/v1/lyrics/song/{song_id}")
    assert response.json()["data"]["available"] is False


def test_visibility_authorized_no_expiration_stays_visible(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, language_id = _seed(db_session)
    _register(client_with_db, "author10@example.com", "author10")
    create_resp = client_with_db.post(
        "/api/v1/lyrics",
        json={"song_id": song_id, "language_id": language_id, "content": "no expiry", "source_type": "ORIGINAL"},
    )
    lyrics_id = create_resp.json()["data"]["id"]
    _run(_set_lyrics_field(db_session, lyrics_id, authorization_status="AUTHORIZED", expiration_date=None))

    client_with_db.cookies.clear()
    response = client_with_db.get(f"/api/v1/lyrics/song/{song_id}")
    assert response.json()["data"]["available"] is True


def test_visibility_authorized_future_expiration_stays_visible(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, language_id = _seed(db_session)
    _register(client_with_db, "author11@example.com", "author11")
    create_resp = client_with_db.post(
        "/api/v1/lyrics",
        json={"song_id": song_id, "language_id": language_id, "content": "future expiry", "source_type": "ORIGINAL"},
    )
    lyrics_id = create_resp.json()["data"]["id"]
    tomorrow = date.today() + timedelta(days=1)
    _run(_set_lyrics_field(db_session, lyrics_id, authorization_status="AUTHORIZED", expiration_date=tomorrow))

    client_with_db.cookies.clear()
    response = client_with_db.get(f"/api/v1/lyrics/song/{song_id}")
    assert response.json()["data"]["available"] is True


def test_visibility_author_sees_own_pending_content(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, language_id = _seed(db_session)
    _register(client_with_db, "author12@example.com", "author12")
    client_with_db.post(
        "/api/v1/lyrics",
        json={"song_id": song_id, "language_id": language_id, "content": "my own pending text", "source_type": "ORIGINAL"},
    )
    response = client_with_db.get(f"/api/v1/lyrics/song/{song_id}")
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["content"] == "my own pending text"
    assert body["authorization_status"] == "PENDING"


def test_visibility_admin_sees_any_status(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, language_id = _seed(db_session)
    _register(client_with_db, "author13@example.com", "author13")
    client_with_db.post(
        "/api/v1/lyrics",
        json={"song_id": song_id, "language_id": language_id, "content": "admin should see this", "source_type": "ORIGINAL"},
    )

    admin = _admin_client(client_with_db, db_session, suffix="v")
    response = admin.get(f"/api/v1/lyrics/song/{song_id}")
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["content"] == "admin should see this"
    assert body["authorization_status"] == "PENDING"


def test_visibility_other_authenticated_user_cannot_see_pending_of_someone_else(
    client_with_db: TestClient, db_session: AsyncSession
) -> None:
    song_id, language_id = _seed(db_session)
    _register(client_with_db, "author14@example.com", "author14")
    client_with_db.post(
        "/api/v1/lyrics",
        json={"song_id": song_id, "language_id": language_id, "content": "private to author14", "source_type": "ORIGINAL"},
    )

    _register(client_with_db, "intruder@example.com", "intruder1")
    response = client_with_db.get(f"/api/v1/lyrics/song/{song_id}")
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["available"] is False
    assert "private to author14" not in response.text


# --------------------------------------------------------------------- EDIT


def test_update_author_can_edit_while_pending(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, language_id = _seed(db_session)
    _register(client_with_db, "editor1@example.com", "editor1")
    create_resp = client_with_db.post(
        "/api/v1/lyrics",
        json={"song_id": song_id, "language_id": language_id, "content": "original text", "source_type": "ORIGINAL"},
    )
    lyrics_id = create_resp.json()["data"]["id"]

    response = client_with_db.put(f"/api/v1/lyrics/{lyrics_id}", json={"content": "corrected text"})
    assert response.status_code == 200
    assert response.json()["data"]["content"] == "corrected text"


def test_update_author_cannot_edit_after_reviewed(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, language_id = _seed(db_session)
    _register(client_with_db, "editor2@example.com", "editor2")
    create_resp = client_with_db.post(
        "/api/v1/lyrics",
        json={"song_id": song_id, "language_id": language_id, "content": "text", "source_type": "ORIGINAL"},
    )
    lyrics_id = create_resp.json()["data"]["id"]
    _run(_set_lyrics_field(db_session, lyrics_id, authorization_status="AUTHORIZED"))

    response = client_with_db.put(f"/api/v1/lyrics/{lyrics_id}", json={"content": "trying to edit"})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "LYRICS_ALREADY_REVIEWED"


def test_update_admin_can_edit_while_pending(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, language_id = _seed(db_session)
    _register(client_with_db, "editor3@example.com", "editor3")
    create_resp = client_with_db.post(
        "/api/v1/lyrics",
        json={"song_id": song_id, "language_id": language_id, "content": "text", "source_type": "ORIGINAL"},
    )
    lyrics_id = create_resp.json()["data"]["id"]

    admin = _admin_client(client_with_db, db_session, suffix="e")
    response = admin.put(f"/api/v1/lyrics/{lyrics_id}", json={"content": "admin corrected"})
    assert response.status_code == 200
    assert response.json()["data"]["content"] == "admin corrected"


def test_update_third_party_forbidden(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, language_id = _seed(db_session)
    _register(client_with_db, "editor4@example.com", "editor4")
    create_resp = client_with_db.post(
        "/api/v1/lyrics",
        json={"song_id": song_id, "language_id": language_id, "content": "text", "source_type": "ORIGINAL"},
    )
    lyrics_id = create_resp.json()["data"]["id"]

    _register(client_with_db, "intruder2@example.com", "intruder2")
    response = client_with_db.put(f"/api/v1/lyrics/{lyrics_id}", json={"content": "hacked"})
    assert response.status_code == 403


def test_update_unknown_lyrics_returns_404(client_with_db: TestClient, db_session: AsyncSession) -> None:
    _seed(db_session)
    _register(client_with_db, "editor5@example.com", "editor5")
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client_with_db.put(f"/api/v1/lyrics/{fake_id}", json={"content": "x"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "LYRICS_NOT_FOUND"


def test_update_cannot_change_protected_fields(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, language_id = _seed(db_session)
    _register(client_with_db, "editor6@example.com", "editor6")
    create_resp = client_with_db.post(
        "/api/v1/lyrics",
        json={"song_id": song_id, "language_id": language_id, "content": "text", "source_type": "ORIGINAL"},
    )
    lyrics_id = create_resp.json()["data"]["id"]
    fake_user_id = "22222222-2222-2222-2222-222222222222"

    response = client_with_db.put(
        f"/api/v1/lyrics/{lyrics_id}",
        json={
            "content": "still my content",
            "authorization_status": "AUTHORIZED",
            "submitted_by_user_id": fake_user_id,
            "song_id": fake_user_id,
        },
    )
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["authorization_status"] == "PENDING"
    assert body["submitted_by_user_id"] != fake_user_id
    assert body["song_id"] == song_id


def test_update_requires_auth(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, language_id = _seed(db_session)
    _register(client_with_db, "editor7@example.com", "editor7")
    create_resp = client_with_db.post(
        "/api/v1/lyrics",
        json={"song_id": song_id, "language_id": language_id, "content": "text", "source_type": "ORIGINAL"},
    )
    lyrics_id = create_resp.json()["data"]["id"]
    client_with_db.cookies.clear()
    response = client_with_db.put(f"/api/v1/lyrics/{lyrics_id}", json={"content": "x"})
    assert response.status_code == 401


# --------------------------------------------------------------------- MINE


def test_list_mine_returns_only_own_submissions(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, language_id = _seed(db_session)
    _register(client_with_db, "mine1@example.com", "mineuser1")
    client_with_db.post(
        "/api/v1/lyrics",
        json={"song_id": song_id, "language_id": language_id, "content": "mine", "source_type": "ORIGINAL"},
    )

    _register(client_with_db, "mine2@example.com", "mineuser2")
    response = client_with_db.get("/api/v1/lyrics/mine")
    assert response.status_code == 200
    assert response.json()["data"] == []
    assert response.json()["meta"]["total"] == 0


def test_list_mine_shows_all_statuses(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, language_id = _seed(db_session)
    _register(client_with_db, "mine3@example.com", "mineuser3")
    create_resp = client_with_db.post(
        "/api/v1/lyrics",
        json={"song_id": song_id, "language_id": language_id, "content": "mine pending", "source_type": "ORIGINAL"},
    )
    lyrics_id = create_resp.json()["data"]["id"]
    _run(_set_lyrics_field(db_session, lyrics_id, authorization_status="REJECTED"))

    response = client_with_db.get("/api/v1/lyrics/mine")
    assert response.json()["meta"]["total"] == 1
    assert response.json()["data"][0]["authorization_status"] == "REJECTED"


def test_list_mine_requires_auth(client_with_db: TestClient) -> None:
    response = client_with_db.get("/api/v1/lyrics/mine")
    assert response.status_code == 401


def test_list_mine_pagination(client_with_db: TestClient, db_session: AsyncSession) -> None:
    from uuid import UUID

    _register(client_with_db, "mine4@example.com", "mineuser4")
    me = UUID(client_with_db.get("/api/v1/auth/me").json()["data"]["id"])

    async def _create_extra_songs_and_lyrics() -> None:
        language = Language(code="fr", name="Français")
        category = Category(name="Adoration")
        db_session.add_all([language, category])
        await db_session.flush()
        artist = Artist(name="CeCe Winans", slug="cece-winans")
        db_session.add(artist)
        await db_session.flush()
        for i in range(3):
            song = Song(
                title=f"Song {i}",
                slug=f"song-{i}",
                artist_id=artist.id,
                category_id=category.id,
                original_language_id=language.id,
                status="PUBLISHED",
            )
            db_session.add(song)
            await db_session.flush()
            lyrics = Lyrics(
                song_id=song.id,
                language_id=language.id,
                content=f"content {i}",
                source_type="ORIGINAL",
                submitted_by_user_id=me,
            )
            db_session.add(lyrics)
        await db_session.commit()

    _run(_create_extra_songs_and_lyrics())

    response = client_with_db.get("/api/v1/lyrics/mine?page=1&page_size=2")
    body = response.json()
    assert len(body["data"]) == 2
    assert body["meta"]["total"] == 3
    assert body["meta"]["total_pages"] == 2


# --------------------------------------------------------------- SECURITY


def test_lyrics_responses_never_leak_password_or_hash(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, language_id = _seed(db_session)
    _register(client_with_db, "secuser@example.com", "secuser1", password="SuperSecretPass1")
    r1 = client_with_db.post(
        "/api/v1/lyrics",
        json={"song_id": song_id, "language_id": language_id, "content": "text", "source_type": "ORIGINAL"},
    )
    r2 = client_with_db.get("/api/v1/lyrics/mine")
    r3 = client_with_db.get(f"/api/v1/lyrics/song/{song_id}")
    for response in (r1, r2, r3):
        assert "SuperSecretPass1" not in response.text
        assert "password_hash" not in response.text


# ------------------------------------------------------------ NON-REGRESSION


def test_health_still_works(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_catalog_still_works(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, _ = _seed(db_session)
    response = client_with_db.get("/api/v1/songs")
    assert response.status_code == 200
    assert response.json()["meta"]["total"] == 1


def test_auth_still_works(client_with_db: TestClient) -> None:
    response = client_with_db.post(
        "/api/v1/auth/register",
        json={"email": "regcheck2@example.com", "username": "regcheck2", "password": "Password123"},
    )
    assert response.status_code == 201
