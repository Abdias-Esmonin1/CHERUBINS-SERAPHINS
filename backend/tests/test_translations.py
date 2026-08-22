"""Tests Phase 5 — Translations (soumission, visibilité, édition, /mine).

Conformément à la validation Option A (symétrique à la Phase 4) :
aucune transition de statut n'est possible via l'API dans cette phase
(pas d'endpoint authorize/reject/revoke — Phase 7). Les tests de
visibilité AUTHORIZED/EXPIRED manipulent donc directement l'état en
base, comme explicitement autorisé.
"""

import asyncio
from datetime import date, timedelta
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Artist, Category, Language, Lyrics, Role, Song, Translation, User

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
        "email": f"tadmin{suffix}@example.com",
        "username": f"tadmin{suffix or '1'}",
        "password": "AdminPass123",
    }
    client_with_db.post("/api/v1/auth/register", json=payload)
    asyncio.get_event_loop().run_until_complete(_promote_to_admin(db_session, payload["email"]))
    client_with_db.cookies.clear()
    client_with_db.post("/api/v1/auth/login", json={"email": payload["email"], "password": payload["password"]})
    return client_with_db


async def _seed(db_session: AsyncSession) -> tuple[str, str, str]:
    """Crée langue originale/cible/catégorie/artiste/chanson PUBLISHED.
    Retourne (song_id, original_language_id, target_language_id)."""
    original_language = Language(code="en", name="English")
    target_language = Language(code="fr", name="Français")
    category = Category(name="Louange")
    db_session.add_all([original_language, target_language, category])
    await db_session.flush()

    artist = Artist(name="Sinach", slug="sinach")
    db_session.add(artist)
    await db_session.flush()

    song = Song(
        title="Way Maker",
        slug="way-maker",
        artist_id=artist.id,
        category_id=category.id,
        original_language_id=original_language.id,
        status="PUBLISHED",
    )
    db_session.add(song)
    await db_session.commit()
    await db_session.refresh(song)
    await db_session.refresh(target_language)
    return str(song.id), str(original_language.id), str(target_language.id)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def _register(client_with_db: TestClient, email: str, username: str, password: str = "Password123") -> None:
    client_with_db.cookies.clear()
    client_with_db.post("/api/v1/auth/register", json={"email": email, "username": username, "password": password})


async def _create_lyrics_direct(
    db_session: AsyncSession, song_id: str, language_id: str, submitted_by_email: str, status: str = "PENDING"
) -> str:
    result = await db_session.execute(select(User).where(User.email == submitted_by_email))
    user = result.scalar_one()
    lyrics = Lyrics(
        song_id=UUID(song_id),
        language_id=UUID(language_id),
        content="original lyrics content",
        source_type="ORIGINAL",
        authorization_status=status,
        submitted_by_user_id=user.id,
    )
    db_session.add(lyrics)
    await db_session.commit()
    await db_session.refresh(lyrics)
    return str(lyrics.id)


def _create_lyrics(
    client_with_db: TestClient, db_session: AsyncSession, song_id: str, language_id: str, email: str, status: str = "PENDING"
) -> str:
    return _run(_create_lyrics_direct(db_session, song_id, language_id, email, status=status))


async def _set_translation_field(db_session: AsyncSession, translation_id: str, **fields) -> None:
    result = await db_session.execute(select(Translation).where(Translation.id == UUID(translation_id)))
    translation = result.scalar_one()
    for key, value in fields.items():
        setattr(translation, key, value)
    await db_session.commit()


def _submit_translation(client_with_db: TestClient, lyrics_id: str, target_language_id: str, content: str = "contenu traduit") -> dict:
    response = client_with_db.post(
        "/api/v1/translations",
        json={
            "lyrics_id": lyrics_id,
            "target_language_id": target_language_id,
            "content": content,
            "translation_type": "HUMAN",
        },
    )
    return response


# ------------------------------------------------------------------- SUBMIT


def test_submit_translation_valid_forces_pending_and_submitter(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "tauthor1@example.com", "tauthor1")
    lyrics_id = _create_lyrics(client_with_db, db_session, song_id, lang_id, "tauthor1@example.com")

    response = _submit_translation(client_with_db, lyrics_id, target_lang_id)
    assert response.status_code == 201
    body = response.json()["data"]
    assert body["authorization_status"] == "PENDING"
    me = client_with_db.get("/api/v1/auth/me").json()["data"]
    assert body["submitted_by_user_id"] == me["id"]


def test_submit_translation_requires_auth(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "tauthor2@example.com", "tauthor2")
    lyrics_id = _create_lyrics(client_with_db, db_session, song_id, lang_id, "tauthor2@example.com")
    client_with_db.cookies.clear()

    response = _submit_translation(client_with_db, lyrics_id, target_lang_id)
    assert response.status_code == 401


def test_submit_translation_unknown_lyrics_returns_404(client_with_db: TestClient, db_session: AsyncSession) -> None:
    _, _, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "tauthor3@example.com", "tauthor3")
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = _submit_translation(client_with_db, fake_id, target_lang_id)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "LYRICS_NOT_FOUND"


def test_submit_translation_unknown_language_returns_404(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, _ = _run(_seed(db_session))
    _register(client_with_db, "tauthor4@example.com", "tauthor4")
    lyrics_id = _create_lyrics(client_with_db, db_session, song_id, lang_id, "tauthor4@example.com")
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = _submit_translation(client_with_db, lyrics_id, fake_id)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "LANGUAGE_NOT_FOUND"


def test_submit_translation_duplicate_language_returns_409(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "tauthor5@example.com", "tauthor5")
    lyrics_id = _create_lyrics(client_with_db, db_session, song_id, lang_id, "tauthor5@example.com")
    _submit_translation(client_with_db, lyrics_id, target_lang_id)
    response = _submit_translation(client_with_db, lyrics_id, target_lang_id)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "TRANSLATION_ALREADY_EXISTS"


def test_submit_translation_invalid_type_returns_422(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "tauthor6@example.com", "tauthor6")
    lyrics_id = _create_lyrics(client_with_db, db_session, song_id, lang_id, "tauthor6@example.com")
    response = client_with_db.post(
        "/api/v1/translations",
        json={
            "lyrics_id": lyrics_id,
            "target_language_id": target_lang_id,
            "content": "x",
            "translation_type": "NOT_A_TYPE",
        },
    )
    assert response.status_code == 422


def test_submit_translation_client_cannot_set_status_or_submitter(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "tauthor7@example.com", "tauthor7")
    lyrics_id = _create_lyrics(client_with_db, db_session, song_id, lang_id, "tauthor7@example.com")
    fake_user_id = "11111111-1111-1111-1111-111111111111"
    response = client_with_db.post(
        "/api/v1/translations",
        json={
            "lyrics_id": lyrics_id,
            "target_language_id": target_lang_id,
            "content": "x",
            "translation_type": "HUMAN",
            "authorization_status": "AUTHORIZED",
            "submitted_by_user_id": fake_user_id,
        },
    )
    assert response.status_code == 201
    body = response.json()["data"]
    assert body["authorization_status"] == "PENDING"
    assert body["submitted_by_user_id"] != fake_user_id


def test_submit_translation_allowed_even_if_lyrics_not_authorized(client_with_db: TestClient, db_session: AsyncSession) -> None:
    """Décision validée : soumettre une traduction ne requiert pas que
    les paroles originales soient elles-mêmes AUTHORIZED."""
    song_id, lang_id, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "tauthor8@example.com", "tauthor8")
    lyrics_id = _create_lyrics(client_with_db, db_session, song_id, lang_id, "tauthor8@example.com", status="PENDING")
    response = _submit_translation(client_with_db, lyrics_id, target_lang_id)
    assert response.status_code == 201


# ---------------------------------------------------------------- VISIBILITY


def test_visibility_no_translations_returns_empty_list(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, _ = _run(_seed(db_session))
    _register(client_with_db, "tauthor9@example.com", "tauthor9")
    lyrics_id = _create_lyrics(client_with_db, db_session, song_id, lang_id, "tauthor9@example.com")
    response = client_with_db.get(f"/api/v1/translations/lyrics/{lyrics_id}")
    assert response.status_code == 200
    assert response.json()["data"] == []


def test_visibility_lyrics_not_found_returns_404(client_with_db: TestClient) -> None:
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client_with_db.get(f"/api/v1/translations/lyrics/{fake_id}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "LYRICS_NOT_FOUND"


def test_visibility_pending_hidden_from_public(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "tauthor10@example.com", "tauthor10")
    lyrics_id = _create_lyrics(client_with_db, db_session, song_id, lang_id, "tauthor10@example.com")
    _submit_translation(client_with_db, lyrics_id, target_lang_id, content="secret translation")

    client_with_db.cookies.clear()
    response = client_with_db.get(f"/api/v1/translations/lyrics/{lyrics_id}")
    assert response.status_code == 200
    items = response.json()["data"]
    assert len(items) == 1
    assert items[0]["available"] is False
    assert "secret translation" not in response.text


def test_visibility_authorized_visible_to_public(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "tauthor11@example.com", "tauthor11")
    lyrics_id = _create_lyrics(client_with_db, db_session, song_id, lang_id, "tauthor11@example.com")
    create_resp = _submit_translation(client_with_db, lyrics_id, target_lang_id, content="public translation")
    translation_id = create_resp.json()["data"]["id"]

    _run(_set_translation_field(db_session, translation_id, authorization_status="AUTHORIZED"))

    client_with_db.cookies.clear()
    response = client_with_db.get(f"/api/v1/translations/lyrics/{lyrics_id}")
    items = response.json()["data"]
    assert items[0]["available"] is True
    assert items[0]["content"] == "public translation"
    assert items[0]["translation_type"] == "HUMAN"
    assert items[0]["target_language"]["code"] == "fr"


def test_visibility_authorized_but_expired_hidden_from_public(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "tauthor12@example.com", "tauthor12")
    lyrics_id = _create_lyrics(client_with_db, db_session, song_id, lang_id, "tauthor12@example.com")
    create_resp = _submit_translation(client_with_db, lyrics_id, target_lang_id)
    translation_id = create_resp.json()["data"]["id"]

    yesterday = date.today() - timedelta(days=1)
    _run(_set_translation_field(db_session, translation_id, authorization_status="AUTHORIZED", expiration_date=yesterday))

    client_with_db.cookies.clear()
    response = client_with_db.get(f"/api/v1/translations/lyrics/{lyrics_id}")
    assert response.json()["data"][0]["available"] is False


def test_visibility_authorized_no_expiration_stays_visible(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "tauthor13@example.com", "tauthor13")
    lyrics_id = _create_lyrics(client_with_db, db_session, song_id, lang_id, "tauthor13@example.com")
    create_resp = _submit_translation(client_with_db, lyrics_id, target_lang_id)
    translation_id = create_resp.json()["data"]["id"]
    _run(_set_translation_field(db_session, translation_id, authorization_status="AUTHORIZED", expiration_date=None))

    client_with_db.cookies.clear()
    response = client_with_db.get(f"/api/v1/translations/lyrics/{lyrics_id}")
    assert response.json()["data"][0]["available"] is True


def test_visibility_author_sees_own_pending_content(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "tauthor14@example.com", "tauthor14")
    lyrics_id = _create_lyrics(client_with_db, db_session, song_id, lang_id, "tauthor14@example.com")
    _submit_translation(client_with_db, lyrics_id, target_lang_id, content="my own pending translation")

    response = client_with_db.get(f"/api/v1/translations/lyrics/{lyrics_id}")
    items = response.json()["data"]
    assert items[0]["content"] == "my own pending translation"
    assert items[0]["authorization_status"] == "PENDING"


def test_visibility_admin_sees_any_status(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "tauthor15@example.com", "tauthor15")
    lyrics_id = _create_lyrics(client_with_db, db_session, song_id, lang_id, "tauthor15@example.com")
    _submit_translation(client_with_db, lyrics_id, target_lang_id, content="admin should see this")

    admin = _admin_client(client_with_db, db_session, suffix="v")
    response = admin.get(f"/api/v1/translations/lyrics/{lyrics_id}")
    items = response.json()["data"]
    assert items[0]["content"] == "admin should see this"
    assert items[0]["authorization_status"] == "PENDING"


def test_visibility_other_authenticated_user_cannot_see_pending_of_someone_else(
    client_with_db: TestClient, db_session: AsyncSession
) -> None:
    song_id, lang_id, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "tauthor16@example.com", "tauthor16")
    lyrics_id = _create_lyrics(client_with_db, db_session, song_id, lang_id, "tauthor16@example.com")
    _submit_translation(client_with_db, lyrics_id, target_lang_id, content="private to tauthor16")

    _register(client_with_db, "tintruder@example.com", "tintruder1")
    response = client_with_db.get(f"/api/v1/translations/lyrics/{lyrics_id}")
    items = response.json()["data"]
    assert items[0]["available"] is False
    assert "private to tauthor16" not in response.text


def test_visibility_multiple_languages_mixed_status(client_with_db: TestClient, db_session: AsyncSession) -> None:
    """Deux traductions indépendantes (langues différentes, auteurs
    différents, statuts différents) doivent être visibles
    indépendamment l'une de l'autre."""
    song_id, lang_id, target_lang_id = _run(_seed(db_session))

    async def _add_third_language() -> str:
        third = Language(code="es", name="Español")
        db_session.add(third)
        await db_session.commit()
        await db_session.refresh(third)
        return str(third.id)

    third_lang_id = _run(_add_third_language())

    _register(client_with_db, "tauthor17@example.com", "tauthor17")
    lyrics_id = _create_lyrics(client_with_db, db_session, song_id, lang_id, "tauthor17@example.com")
    fr_resp = _submit_translation(client_with_db, lyrics_id, target_lang_id, content="french content")
    fr_id = fr_resp.json()["data"]["id"]
    _run(_set_translation_field(db_session, fr_id, authorization_status="AUTHORIZED"))

    _register(client_with_db, "tauthor18@example.com", "tauthor18")
    es_resp = _submit_translation(client_with_db, lyrics_id, third_lang_id, content="spanish content")
    assert es_resp.status_code == 201  # tauthor18 n'est pas l'auteur des paroles, mais peut soumettre une traduction

    client_with_db.cookies.clear()
    response = client_with_db.get(f"/api/v1/translations/lyrics/{lyrics_id}")
    items = response.json()["data"]
    assert len(items) == 2
    by_lang = {item["target_language"]["code"]: item for item in items}
    assert by_lang["fr"]["available"] is True
    assert by_lang["fr"]["content"] == "french content"
    assert by_lang["es"]["available"] is False
    assert "content" not in by_lang["es"] or by_lang["es"]["content"] is None


def test_visibility_filter_by_target_language_id(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, target_lang_id = _run(_seed(db_session))

    async def _add_third_language() -> str:
        third = Language(code="pt", name="Português")
        db_session.add(third)
        await db_session.commit()
        await db_session.refresh(third)
        return str(third.id)

    third_lang_id = _run(_add_third_language())

    _register(client_with_db, "tauthor19@example.com", "tauthor19")
    lyrics_id = _create_lyrics(client_with_db, db_session, song_id, lang_id, "tauthor19@example.com")
    _submit_translation(client_with_db, lyrics_id, target_lang_id)
    _submit_translation(client_with_db, lyrics_id, third_lang_id)

    response = client_with_db.get(f"/api/v1/translations/lyrics/{lyrics_id}?target_language_id={target_lang_id}")
    items = response.json()["data"]
    assert len(items) == 1
    assert items[0]["target_language"]["code"] == "fr"


# --------------------------------------------------------------------- EDIT


def test_update_author_can_edit_while_pending(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "teditor1@example.com", "teditor1")
    lyrics_id = _create_lyrics(client_with_db, db_session, song_id, lang_id, "teditor1@example.com")
    create_resp = _submit_translation(client_with_db, lyrics_id, target_lang_id, content="original translation")
    translation_id = create_resp.json()["data"]["id"]

    response = client_with_db.put(f"/api/v1/translations/{translation_id}", json={"content": "corrected translation"})
    assert response.status_code == 200
    assert response.json()["data"]["content"] == "corrected translation"


def test_update_author_cannot_edit_after_reviewed(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "teditor2@example.com", "teditor2")
    lyrics_id = _create_lyrics(client_with_db, db_session, song_id, lang_id, "teditor2@example.com")
    create_resp = _submit_translation(client_with_db, lyrics_id, target_lang_id)
    translation_id = create_resp.json()["data"]["id"]
    _run(_set_translation_field(db_session, translation_id, authorization_status="AUTHORIZED"))

    response = client_with_db.put(f"/api/v1/translations/{translation_id}", json={"content": "trying to edit"})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "TRANSLATION_ALREADY_REVIEWED"


def test_update_admin_can_edit_while_pending(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "teditor3@example.com", "teditor3")
    lyrics_id = _create_lyrics(client_with_db, db_session, song_id, lang_id, "teditor3@example.com")
    create_resp = _submit_translation(client_with_db, lyrics_id, target_lang_id)
    translation_id = create_resp.json()["data"]["id"]

    admin = _admin_client(client_with_db, db_session, suffix="e")
    response = admin.put(f"/api/v1/translations/{translation_id}", json={"content": "admin corrected"})
    assert response.status_code == 200
    assert response.json()["data"]["content"] == "admin corrected"


def test_update_third_party_forbidden(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "teditor4@example.com", "teditor4")
    lyrics_id = _create_lyrics(client_with_db, db_session, song_id, lang_id, "teditor4@example.com")
    create_resp = _submit_translation(client_with_db, lyrics_id, target_lang_id)
    translation_id = create_resp.json()["data"]["id"]

    _register(client_with_db, "tintruder2@example.com", "tintruder2")
    response = client_with_db.put(f"/api/v1/translations/{translation_id}", json={"content": "hacked"})
    assert response.status_code == 403


def test_update_unknown_translation_returns_404(client_with_db: TestClient, db_session: AsyncSession) -> None:
    _register(client_with_db, "teditor5@example.com", "teditor5")
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client_with_db.put(f"/api/v1/translations/{fake_id}", json={"content": "x"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TRANSLATION_NOT_FOUND"


def test_update_cannot_change_protected_fields(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "teditor6@example.com", "teditor6")
    lyrics_id = _create_lyrics(client_with_db, db_session, song_id, lang_id, "teditor6@example.com")
    create_resp = _submit_translation(client_with_db, lyrics_id, target_lang_id)
    translation_id = create_resp.json()["data"]["id"]
    fake_user_id = "22222222-2222-2222-2222-222222222222"

    response = client_with_db.put(
        f"/api/v1/translations/{translation_id}",
        json={
            "content": "still my content",
            "authorization_status": "AUTHORIZED",
            "submitted_by_user_id": fake_user_id,
            "lyrics_id": fake_user_id,
        },
    )
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["authorization_status"] == "PENDING"
    assert body["submitted_by_user_id"] != fake_user_id
    assert body["lyrics_id"] == lyrics_id


def test_update_requires_auth(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "teditor7@example.com", "teditor7")
    lyrics_id = _create_lyrics(client_with_db, db_session, song_id, lang_id, "teditor7@example.com")
    create_resp = _submit_translation(client_with_db, lyrics_id, target_lang_id)
    translation_id = create_resp.json()["data"]["id"]
    client_with_db.cookies.clear()
    response = client_with_db.put(f"/api/v1/translations/{translation_id}", json={"content": "x"})
    assert response.status_code == 401


# --------------------------------------------------------------------- MINE


def test_list_mine_returns_only_own_submissions(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "tmine1@example.com", "tmineuser1")
    lyrics_id = _create_lyrics(client_with_db, db_session, song_id, lang_id, "tmine1@example.com")
    _submit_translation(client_with_db, lyrics_id, target_lang_id)

    _register(client_with_db, "tmine2@example.com", "tmineuser2")
    response = client_with_db.get("/api/v1/translations/mine")
    assert response.status_code == 200
    assert response.json()["data"] == []
    assert response.json()["meta"]["total"] == 0


def test_list_mine_shows_all_statuses(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "tmine3@example.com", "tmineuser3")
    lyrics_id = _create_lyrics(client_with_db, db_session, song_id, lang_id, "tmine3@example.com")
    create_resp = _submit_translation(client_with_db, lyrics_id, target_lang_id)
    translation_id = create_resp.json()["data"]["id"]
    _run(_set_translation_field(db_session, translation_id, authorization_status="REJECTED"))

    response = client_with_db.get("/api/v1/translations/mine")
    assert response.json()["meta"]["total"] == 1
    assert response.json()["data"][0]["authorization_status"] == "REJECTED"


def test_list_mine_requires_auth(client_with_db: TestClient) -> None:
    response = client_with_db.get("/api/v1/translations/mine")
    assert response.status_code == 401


def test_list_mine_pagination(client_with_db: TestClient, db_session: AsyncSession) -> None:
    _register(client_with_db, "tmine4@example.com", "tmineuser4")
    me = UUID(client_with_db.get("/api/v1/auth/me").json()["data"]["id"])

    async def _create_extra() -> None:
        original_language = Language(code="de", name="Deutsch")
        category = Category(name="Adoration2")
        db_session.add_all([original_language, category])
        await db_session.flush()
        artist = Artist(name="CeCe Winans T", slug="cece-winans-t")
        db_session.add(artist)
        await db_session.flush()
        for i in range(3):
            song = Song(
                title=f"TSong {i}",
                slug=f"tsong-{i}",
                artist_id=artist.id,
                category_id=category.id,
                original_language_id=original_language.id,
                status="PUBLISHED",
            )
            db_session.add(song)
            await db_session.flush()
            lyrics = Lyrics(
                song_id=song.id,
                language_id=original_language.id,
                content=f"lyrics {i}",
                source_type="ORIGINAL",
                submitted_by_user_id=me,
            )
            db_session.add(lyrics)
            await db_session.flush()
            target = Language(code=f"x{i}", name=f"Lang{i}")
            db_session.add(target)
            await db_session.flush()
            translation = Translation(
                lyrics_id=lyrics.id,
                target_language_id=target.id,
                content=f"translation {i}",
                translation_type="HUMAN",
                submitted_by_user_id=me,
            )
            db_session.add(translation)
        await db_session.commit()

    _run(_create_extra())

    response = client_with_db.get("/api/v1/translations/mine?page=1&page_size=2")
    body = response.json()
    assert len(body["data"]) == 2
    assert body["meta"]["total"] == 3
    assert body["meta"]["total_pages"] == 2


# --------------------------------------------------------------- SECURITY


def test_translation_responses_never_leak_password_or_hash(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "tsecuser@example.com", "tsecuser1", password="SuperSecretPass2")
    lyrics_id = _create_lyrics(client_with_db, db_session, song_id, lang_id, "tsecuser@example.com")
    r1 = _submit_translation(client_with_db, lyrics_id, target_lang_id)
    r2 = client_with_db.get("/api/v1/translations/mine")
    r3 = client_with_db.get(f"/api/v1/translations/lyrics/{lyrics_id}")
    for response in (r1, r2, r3):
        assert "SuperSecretPass2" not in response.text
        assert "password_hash" not in response.text


# ------------------------------------------------------------ NON-REGRESSION


def test_health_still_works(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_catalog_still_works(client_with_db: TestClient, db_session: AsyncSession) -> None:
    _run(_seed(db_session))
    response = client_with_db.get("/api/v1/songs")
    assert response.status_code == 200
    assert response.json()["meta"]["total"] == 1


def test_auth_still_works(client_with_db: TestClient) -> None:
    response = client_with_db.post(
        "/api/v1/auth/register",
        json={"email": "tregcheck@example.com", "username": "tregcheck", "password": "Password123"},
    )
    assert response.status_code == 201


def test_lyrics_still_works(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, _ = _run(_seed(db_session))
    _register(client_with_db, "tlyricscheck@example.com", "tlyricscheck")
    response = client_with_db.post(
        "/api/v1/lyrics",
        json={"song_id": song_id, "language_id": lang_id, "content": "x", "source_type": "ORIGINAL"},
    )
    assert response.status_code == 201
