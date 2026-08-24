"""Tests Phase 7 — Administration / Rights Records / Modération.

Couvre : authorize/reject/revoke pour Lyrics ET Translation,
traçabilité systématique via RightsRecord (append-only), listing
admin, statistiques, IDOR, cohérence transactionnelle, non-régression.
"""

import asyncio
from datetime import date, timedelta
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Artist, Category, Language, RightsRecord, Role, Song, User

# ------------------------------------------------------------------- HELPERS


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


async def _promote_to_admin(db_session: AsyncSession, email: str) -> None:
    result = await db_session.execute(select(Role).where(Role.name == "ADMIN"))
    admin_role = result.scalar_one()
    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalar_one()
    user.role_id = admin_role.id
    await db_session.commit()


def _admin_client(client_with_db: TestClient, db_session: AsyncSession, suffix: str = "") -> TestClient:
    payload = {
        "email": f"madmin{suffix}@example.com",
        "username": f"madmin{suffix or '1'}",
        "password": "AdminPass123",
    }
    client_with_db.post("/api/v1/auth/register", json=payload)
    _run(_promote_to_admin(db_session, payload["email"]))
    client_with_db.cookies.clear()
    client_with_db.post("/api/v1/auth/login", json={"email": payload["email"], "password": payload["password"]})
    return client_with_db


def _register(client_with_db: TestClient, email: str, username: str, password: str = "Password123") -> None:
    client_with_db.cookies.clear()
    client_with_db.post("/api/v1/auth/register", json={"email": email, "username": username, "password": password})


async def _seed(db_session: AsyncSession) -> tuple[str, str, str]:
    """Retourne (song_id, original_language_id, target_language_id)."""
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


def _submit_lyrics(client_with_db: TestClient, song_id: str, language_id: str, content: str = "lyrics content") -> dict:
    response = client_with_db.post(
        "/api/v1/lyrics",
        json={"song_id": song_id, "language_id": language_id, "content": content, "source_type": "ORIGINAL"},
    )
    assert response.status_code == 201
    return response.json()["data"]


def _submit_translation(client_with_db: TestClient, lyrics_id: str, target_language_id: str, content: str = "translation content") -> dict:
    response = client_with_db.post(
        "/api/v1/translations",
        json={
            "lyrics_id": lyrics_id,
            "target_language_id": target_language_id,
            "content": content,
            "translation_type": "HUMAN",
        },
    )
    assert response.status_code == 201
    return response.json()["data"]


async def _get_rights_records_for_lyrics(db_session: AsyncSession, lyrics_id: str) -> list[RightsRecord]:
    result = await db_session.execute(select(RightsRecord).where(RightsRecord.lyrics_id == UUID(lyrics_id)))
    return list(result.scalars().all())


async def _get_rights_records_for_translation(db_session: AsyncSession, translation_id: str) -> list[RightsRecord]:
    result = await db_session.execute(
        select(RightsRecord).where(RightsRecord.translation_id == UUID(translation_id))
    )
    return list(result.scalars().all())


async def _count_rights_records(db_session: AsyncSession) -> int:
    result = await db_session.execute(select(RightsRecord))
    return len(list(result.scalars().all()))


# =================================================================== LYRICS


def test_authorize_lyrics_from_pending(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, _ = _run(_seed(db_session))
    _register(client_with_db, "lauthor1@example.com", "lauthor1")
    lyrics = _submit_lyrics(client_with_db, song_id, lang_id)

    admin = _admin_client(client_with_db, db_session, suffix="a1")
    response = admin.patch(
        f"/api/v1/admin/lyrics/{lyrics['id']}/authorize",
        json={"authorization_reference": "LIC-2026-001", "authorization_date": "2026-08-23", "expiration_date": "2029-08-23"},
    )
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["authorization_status"] == "AUTHORIZED"
    assert body["authorization_reference"] == "LIC-2026-001"
    assert body["authorization_date"] == "2026-08-23"
    assert body["expiration_date"] == "2029-08-23"
    me = admin.get("/api/v1/auth/me").json()["data"]
    assert body["reviewed_by_user_id"] == me["id"]


def test_authorize_lyrics_creates_rights_record(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, _ = _run(_seed(db_session))
    _register(client_with_db, "lauthor2@example.com", "lauthor2")
    lyrics = _submit_lyrics(client_with_db, song_id, lang_id)

    admin = _admin_client(client_with_db, db_session, suffix="a2")
    admin.patch(f"/api/v1/admin/lyrics/{lyrics['id']}/authorize", json={})

    records = _run(_get_rights_records_for_lyrics(db_session, lyrics["id"]))
    assert len(records) == 1
    assert records[0].action == "VALIDATED"
    assert records[0].previous_status == "PENDING"
    assert records[0].new_status == "AUTHORIZED"
    assert records[0].translation_id is None
    me = admin.get("/api/v1/auth/me").json()["data"]
    assert str(records[0].performed_by_user_id) == me["id"]


def test_authorize_lyrics_makes_it_publicly_visible(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, _ = _run(_seed(db_session))
    _register(client_with_db, "lauthor3@example.com", "lauthor3")
    lyrics = _submit_lyrics(client_with_db, song_id, lang_id, content="now public")

    admin = _admin_client(client_with_db, db_session, suffix="a3")
    admin.patch(f"/api/v1/admin/lyrics/{lyrics['id']}/authorize", json={})

    client_with_db.cookies.clear()
    response = client_with_db.get(f"/api/v1/lyrics/song/{song_id}")
    assert response.json()["data"]["available"] is True
    assert response.json()["data"]["content"] == "now public"


def test_reject_lyrics_from_pending_requires_reason(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, _ = _run(_seed(db_session))
    _register(client_with_db, "lauthor4@example.com", "lauthor4")
    lyrics = _submit_lyrics(client_with_db, song_id, lang_id)

    admin = _admin_client(client_with_db, db_session, suffix="a4")
    missing_reason = admin.patch(f"/api/v1/admin/lyrics/{lyrics['id']}/reject", json={})
    assert missing_reason.status_code == 422

    response = admin.patch(f"/api/v1/admin/lyrics/{lyrics['id']}/reject", json={"reason": "Source non vérifiable"})
    assert response.status_code == 200
    assert response.json()["data"]["authorization_status"] == "REJECTED"

    records = _run(_get_rights_records_for_lyrics(db_session, lyrics["id"]))
    assert len(records) == 1
    assert records[0].action == "REJECTED"
    assert records[0].reason == "Source non vérifiable"


def test_revoke_lyrics_from_authorized_requires_reason(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, _ = _run(_seed(db_session))
    _register(client_with_db, "lauthor5@example.com", "lauthor5")
    lyrics = _submit_lyrics(client_with_db, song_id, lang_id)

    admin = _admin_client(client_with_db, db_session, suffix="a5")
    admin.patch(f"/api/v1/admin/lyrics/{lyrics['id']}/authorize", json={})

    missing_reason = admin.patch(f"/api/v1/admin/lyrics/{lyrics['id']}/revoke", json={})
    assert missing_reason.status_code == 422

    response = admin.patch(f"/api/v1/admin/lyrics/{lyrics['id']}/revoke", json={"reason": "Plainte déposée"})
    assert response.status_code == 200
    assert response.json()["data"]["authorization_status"] == "REVOKED"

    records = _run(_get_rights_records_for_lyrics(db_session, lyrics["id"]))
    assert len(records) == 2  # VALIDATED puis REVOKED
    assert records[-1].action == "REVOKED"
    assert records[-1].previous_status == "AUTHORIZED"
    assert records[-1].new_status == "REVOKED"
    assert records[-1].reason == "Plainte déposée"

    # Effet immédiat : plus visible publiquement
    client_with_db.cookies.clear()
    response = client_with_db.get(f"/api/v1/lyrics/song/{song_id}")
    assert response.json()["data"]["available"] is False


def test_authorize_lyrics_restores_from_expired(client_with_db: TestClient, db_session: AsyncSession) -> None:
    """EXPIRED est un statut effectif (calculé), jamais littéralement
    stocké — 'restaurer' signifie ré-autoriser un enregistrement stocké
    AUTHORIZED dont expiration_date est dépassée."""
    song_id, lang_id, _ = _run(_seed(db_session))
    _register(client_with_db, "lauthor6@example.com", "lauthor6")
    lyrics = _submit_lyrics(client_with_db, song_id, lang_id)

    admin = _admin_client(client_with_db, db_session, suffix="a6")
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    admin.patch(f"/api/v1/admin/lyrics/{lyrics['id']}/authorize", json={"expiration_date": yesterday})

    # Fonctionnellement expiré : invisible publiquement
    client_with_db.cookies.clear()
    assert client_with_db.get(f"/api/v1/lyrics/song/{song_id}").json()["data"]["available"] is False

    # L'admin restaure avec une nouvelle date d'expiration future
    # (recréer le client admin car le cookie a été effacé ci-dessus)
    admin = _admin_client(client_with_db, db_session, suffix="a6b")
    future = (date.today() + timedelta(days=30)).isoformat()
    response = admin.patch(f"/api/v1/admin/lyrics/{lyrics['id']}/authorize", json={"expiration_date": future})
    assert response.status_code == 200
    assert response.json()["data"]["authorization_status"] == "AUTHORIZED"

    records = _run(_get_rights_records_for_lyrics(db_session, lyrics["id"]))
    assert records[-1].previous_status == "EXPIRED"
    assert records[-1].new_status == "AUTHORIZED"

    client_with_db.cookies.clear()
    assert client_with_db.get(f"/api/v1/lyrics/song/{song_id}").json()["data"]["available"] is True


def test_invalid_transitions_return_409_and_create_no_rights_record(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, _ = _run(_seed(db_session))
    _register(client_with_db, "lauthor7@example.com", "lauthor7")
    lyrics = _submit_lyrics(client_with_db, song_id, lang_id)

    admin = _admin_client(client_with_db, db_session, suffix="a7")

    # revoke depuis PENDING -> invalide (REVOKE_FROM = {AUTHORIZED})
    before = _run(_count_rights_records(db_session))
    response = admin.patch(f"/api/v1/admin/lyrics/{lyrics['id']}/revoke", json={"reason": "x"})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVALID_TRANSITION"
    after = _run(_count_rights_records(db_session))
    assert after == before  # aucun rights_record créé

    # reject depuis PENDING -> OK, puis reject à nouveau -> invalide (REJECT_FROM = {PENDING})
    admin.patch(f"/api/v1/admin/lyrics/{lyrics['id']}/reject", json={"reason": "premier rejet"})
    before2 = _run(_count_rights_records(db_session))
    response2 = admin.patch(f"/api/v1/admin/lyrics/{lyrics['id']}/reject", json={"reason": "second rejet"})
    assert response2.status_code == 409
    after2 = _run(_count_rights_records(db_session))
    assert after2 == before2


def test_authorize_lyrics_requires_admin(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, _ = _run(_seed(db_session))
    _register(client_with_db, "lauthor8@example.com", "lauthor8")
    lyrics = _submit_lyrics(client_with_db, song_id, lang_id)

    response = client_with_db.patch(f"/api/v1/admin/lyrics/{lyrics['id']}/authorize", json={})
    assert response.status_code == 403  # authentifié mais non-admin

    client_with_db.cookies.clear()
    response_anon = client_with_db.patch(f"/api/v1/admin/lyrics/{lyrics['id']}/authorize", json={})
    assert response_anon.status_code == 401  # non authentifié


def test_authorize_unknown_lyrics_returns_404(client_with_db: TestClient, db_session: AsyncSession) -> None:
    admin = _admin_client(client_with_db, db_session, suffix="a9")
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = admin.patch(f"/api/v1/admin/lyrics/{fake_id}/authorize", json={})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "LYRICS_NOT_FOUND"


# ============================================================== TRANSLATIONS


def test_authorize_translation_from_pending(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "tauthor1@example.com", "tauthor1m")
    lyrics = _submit_lyrics(client_with_db, song_id, lang_id)
    translation = _submit_translation(client_with_db, lyrics["id"], target_lang_id)

    admin = _admin_client(client_with_db, db_session, suffix="ta1")
    response = admin.patch(
        f"/api/v1/admin/translations/{translation['id']}/authorize",
        json={"authorization_reference": "LIC-2026-002", "authorization_date": "2026-08-23", "expiration_date": "2029-08-23"},
    )
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["authorization_status"] == "AUTHORIZED"
    assert body["authorization_reference"] == "LIC-2026-002"
    assert body["authorization_date"] == "2026-08-23"
    assert body["expiration_date"] == "2029-08-23"


def test_authorize_translation_creates_rights_record(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "tauthor2@example.com", "tauthor2m")
    lyrics = _submit_lyrics(client_with_db, song_id, lang_id)
    translation = _submit_translation(client_with_db, lyrics["id"], target_lang_id)

    admin = _admin_client(client_with_db, db_session, suffix="ta2")
    admin.patch(f"/api/v1/admin/translations/{translation['id']}/authorize", json={})

    records = _run(_get_rights_records_for_translation(db_session, translation["id"]))
    assert len(records) == 1
    assert records[0].action == "VALIDATED"
    assert records[0].lyrics_id is None
    assert records[0].previous_status == "PENDING"
    assert records[0].new_status == "AUTHORIZED"


def test_reject_translation_requires_reason(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "tauthor3@example.com", "tauthor3m")
    lyrics = _submit_lyrics(client_with_db, song_id, lang_id)
    translation = _submit_translation(client_with_db, lyrics["id"], target_lang_id)

    admin = _admin_client(client_with_db, db_session, suffix="ta3")
    missing = admin.patch(f"/api/v1/admin/translations/{translation['id']}/reject", json={})
    assert missing.status_code == 422
    response = admin.patch(f"/api/v1/admin/translations/{translation['id']}/reject", json={"reason": "Traduction incorrecte"})
    assert response.status_code == 200
    assert response.json()["data"]["authorization_status"] == "REJECTED"


def test_revoke_translation_requires_reason(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "tauthor4@example.com", "tauthor4m")
    lyrics = _submit_lyrics(client_with_db, song_id, lang_id)
    translation = _submit_translation(client_with_db, lyrics["id"], target_lang_id)

    admin = _admin_client(client_with_db, db_session, suffix="ta4")
    admin.patch(f"/api/v1/admin/translations/{translation['id']}/authorize", json={})
    missing = admin.patch(f"/api/v1/admin/translations/{translation['id']}/revoke", json={})
    assert missing.status_code == 422
    response = admin.patch(f"/api/v1/admin/translations/{translation['id']}/revoke", json={"reason": "Retrait demandé"})
    assert response.status_code == 200
    assert response.json()["data"]["authorization_status"] == "REVOKED"


def test_authorize_translation_restores_from_expired(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "tauthor5@example.com", "tauthor5m")
    lyrics = _submit_lyrics(client_with_db, song_id, lang_id)
    translation = _submit_translation(client_with_db, lyrics["id"], target_lang_id)

    admin = _admin_client(client_with_db, db_session, suffix="ta5")
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    admin.patch(f"/api/v1/admin/translations/{translation['id']}/authorize", json={"expiration_date": yesterday})

    future = (date.today() + timedelta(days=30)).isoformat()
    response = admin.patch(f"/api/v1/admin/translations/{translation['id']}/authorize", json={"expiration_date": future})
    assert response.status_code == 200
    records = _run(_get_rights_records_for_translation(db_session, translation["id"]))
    assert records[-1].previous_status == "EXPIRED"
    assert records[-1].new_status == "AUTHORIZED"


def test_translation_invalid_transition_returns_409(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "tauthor6@example.com", "tauthor6m")
    lyrics = _submit_lyrics(client_with_db, song_id, lang_id)
    translation = _submit_translation(client_with_db, lyrics["id"], target_lang_id)

    admin = _admin_client(client_with_db, db_session, suffix="ta6")
    response = admin.patch(f"/api/v1/admin/translations/{translation['id']}/revoke", json={"reason": "x"})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVALID_TRANSITION"


def test_translation_moderation_requires_admin(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "tauthor7@example.com", "tauthor7m")
    lyrics = _submit_lyrics(client_with_db, song_id, lang_id)
    translation = _submit_translation(client_with_db, lyrics["id"], target_lang_id)

    response = client_with_db.patch(f"/api/v1/admin/translations/{translation['id']}/authorize", json={})
    assert response.status_code == 403


def test_authorize_unknown_translation_returns_404(client_with_db: TestClient, db_session: AsyncSession) -> None:
    admin = _admin_client(client_with_db, db_session, suffix="ta9")
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = admin.patch(f"/api/v1/admin/translations/{fake_id}/authorize", json={})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TRANSLATION_NOT_FOUND"


# ------------------------------------------------------------------ TRANSACTIONAL


def test_transaction_consistency_no_orphan_rights_record_on_invalid_transition(
    client_with_db: TestClient, db_session: AsyncSession
) -> None:
    """Aucun rights_record ne doit exister sans transition réellement
    appliquée, et inversement."""
    song_id, lang_id, _ = _run(_seed(db_session))
    _register(client_with_db, "ltx1@example.com", "ltx1")
    lyrics = _submit_lyrics(client_with_db, song_id, lang_id)
    admin = _admin_client(client_with_db, db_session, suffix="tx1")

    before = _run(_count_rights_records(db_session))
    admin.patch(f"/api/v1/admin/lyrics/{lyrics['id']}/revoke", json={"reason": "invalide depuis PENDING"})
    after = _run(_count_rights_records(db_session))
    assert before == after

    # Une transition valide doit créer EXACTEMENT un rights_record
    admin.patch(f"/api/v1/admin/lyrics/{lyrics['id']}/authorize", json={})
    after_valid = _run(_count_rights_records(db_session))
    assert after_valid == after + 1


# ------------------------------------------------------------- RIGHTS RECORDS


def test_rights_records_are_append_only_no_write_routes(client_with_db: TestClient, db_session: AsyncSession) -> None:
    admin = _admin_client(client_with_db, db_session, suffix="rr1")
    fake_id = "00000000-0000-0000-0000-000000000000"
    assert admin.post("/api/v1/admin/rights-records", json={}).status_code in (404, 405)
    assert admin.put(f"/api/v1/admin/rights-records/{fake_id}", json={}).status_code in (404, 405)
    assert admin.patch(f"/api/v1/admin/rights-records/{fake_id}", json={}).status_code in (404, 405)
    assert admin.delete(f"/api/v1/admin/rights-records/{fake_id}").status_code in (404, 405)


def test_rights_records_listing_and_filters(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, _ = _run(_seed(db_session))
    _register(client_with_db, "rr2author@example.com", "rr2author")
    lyrics = _submit_lyrics(client_with_db, song_id, lang_id)

    admin = _admin_client(client_with_db, db_session, suffix="rr2")
    admin.patch(f"/api/v1/admin/lyrics/{lyrics['id']}/authorize", json={})
    admin.patch(f"/api/v1/admin/lyrics/{lyrics['id']}/revoke", json={"reason": "test filtre"})

    response = admin.get(f"/api/v1/admin/rights-records?lyrics_id={lyrics['id']}")
    assert response.status_code == 200
    assert response.json()["meta"]["total"] == 2

    filtered = admin.get(f"/api/v1/admin/rights-records?lyrics_id={lyrics['id']}&action=REVOKED")
    assert filtered.json()["meta"]["total"] == 1
    assert filtered.json()["data"][0]["action"] == "REVOKED"


def test_rights_records_pagination(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, _ = _run(_seed(db_session))
    _register(client_with_db, "rr3author@example.com", "rr3author")
    lyrics = _submit_lyrics(client_with_db, song_id, lang_id)

    admin = _admin_client(client_with_db, db_session, suffix="rr3")
    admin.patch(f"/api/v1/admin/lyrics/{lyrics['id']}/authorize", json={})
    admin.patch(f"/api/v1/admin/lyrics/{lyrics['id']}/revoke", json={"reason": "x"})

    response = admin.get("/api/v1/admin/rights-records?page=1&page_size=1")
    assert len(response.json()["data"]) == 1
    assert response.json()["meta"]["total_pages"] >= 2


def test_rights_records_requires_admin(client_with_db: TestClient) -> None:
    _register(client_with_db, "rr4@example.com", "rr4user")
    response = client_with_db.get("/api/v1/admin/rights-records")
    assert response.status_code == 403


# ------------------------------------------------------------------- ADMIN


def test_admin_list_lyrics_by_status(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, _ = _run(_seed(db_session))
    _register(client_with_db, "alist1@example.com", "alist1")
    lyrics = _submit_lyrics(client_with_db, song_id, lang_id)

    admin = _admin_client(client_with_db, db_session, suffix="al1")
    pending = admin.get("/api/v1/admin/lyrics?status=PENDING")
    assert pending.json()["meta"]["total"] == 1

    admin.patch(f"/api/v1/admin/lyrics/{lyrics['id']}/authorize", json={})
    pending_after = admin.get("/api/v1/admin/lyrics?status=PENDING")
    assert pending_after.json()["meta"]["total"] == 0
    authorized = admin.get("/api/v1/admin/lyrics?status=AUTHORIZED")
    assert authorized.json()["meta"]["total"] == 1


def test_admin_get_lyrics_detail(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, _ = _run(_seed(db_session))
    _register(client_with_db, "adetail1@example.com", "adetail1")
    lyrics = _submit_lyrics(client_with_db, song_id, lang_id, content="detail content")

    admin = _admin_client(client_with_db, db_session, suffix="ad1")
    response = admin.get(f"/api/v1/admin/lyrics/{lyrics['id']}")
    assert response.status_code == 200
    assert response.json()["data"]["content"] == "detail content"


def test_admin_list_translations_by_status(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "alist2@example.com", "alist2")
    lyrics = _submit_lyrics(client_with_db, song_id, lang_id)
    _submit_translation(client_with_db, lyrics["id"], target_lang_id)

    admin = _admin_client(client_with_db, db_session, suffix="al2")
    pending = admin.get("/api/v1/admin/translations?status=PENDING")
    assert pending.json()["meta"]["total"] == 1


def test_admin_get_translation_detail(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "adetail2@example.com", "adetail2")
    lyrics = _submit_lyrics(client_with_db, song_id, lang_id)
    translation = _submit_translation(client_with_db, lyrics["id"], target_lang_id, content="translation detail")

    admin = _admin_client(client_with_db, db_session, suffix="ad2")
    response = admin.get(f"/api/v1/admin/translations/{translation['id']}")
    assert response.status_code == 200
    assert response.json()["data"]["content"] == "translation detail"


def test_admin_lyrics_and_translations_listing_require_admin(client_with_db: TestClient) -> None:
    _register(client_with_db, "anonadmin@example.com", "anonadmin")
    assert client_with_db.get("/api/v1/admin/lyrics").status_code == 403
    assert client_with_db.get("/api/v1/admin/translations").status_code == 403
    fake_id = "00000000-0000-0000-0000-000000000000"
    assert client_with_db.get(f"/api/v1/admin/lyrics/{fake_id}").status_code == 403
    assert client_with_db.get(f"/api/v1/admin/translations/{fake_id}").status_code == 403


def test_admin_stats(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "stats1@example.com", "stats1")
    lyrics = _submit_lyrics(client_with_db, song_id, lang_id)
    _submit_translation(client_with_db, lyrics["id"], target_lang_id)
    client_with_db.post("/api/v1/favorites", json={"song_id": song_id})

    admin = _admin_client(client_with_db, db_session, suffix="st1")
    admin.patch(f"/api/v1/admin/lyrics/{lyrics['id']}/authorize", json={})

    response = admin.get("/api/v1/admin/stats")
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["songs_count"] == 1
    assert body["artists_count"] == 1
    assert body["favorites_count"] == 1
    assert body["lyrics_by_status_count"]["AUTHORIZED"] == 1
    assert body["lyrics_by_status_count"]["PENDING"] == 0


def test_admin_stats_requires_admin(client_with_db: TestClient) -> None:
    _register(client_with_db, "statsuser@example.com", "statsuser")
    response = client_with_db.get("/api/v1/admin/stats")
    assert response.status_code == 403


# --------------------------------------------------------------------- IDOR


def test_non_admin_cannot_access_any_admin_route(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, target_lang_id = _run(_seed(db_session))
    _register(client_with_db, "idor1@example.com", "idor1")
    lyrics = _submit_lyrics(client_with_db, song_id, lang_id)
    translation = _submit_translation(client_with_db, lyrics["id"], target_lang_id)

    routes = [
        ("get", "/api/v1/admin/lyrics"),
        ("get", f"/api/v1/admin/lyrics/{lyrics['id']}"),
        ("patch", f"/api/v1/admin/lyrics/{lyrics['id']}/authorize"),
        ("patch", f"/api/v1/admin/lyrics/{lyrics['id']}/reject"),
        ("patch", f"/api/v1/admin/lyrics/{lyrics['id']}/revoke"),
        ("get", "/api/v1/admin/translations"),
        ("get", f"/api/v1/admin/translations/{translation['id']}"),
        ("patch", f"/api/v1/admin/translations/{translation['id']}/authorize"),
        ("patch", f"/api/v1/admin/translations/{translation['id']}/reject"),
        ("patch", f"/api/v1/admin/translations/{translation['id']}/revoke"),
        ("get", "/api/v1/admin/rights-records"),
        ("get", "/api/v1/admin/stats"),
    ]
    for method, path in routes:
        if method == "patch":
            response = client_with_db.patch(path, json={})
        else:
            response = client_with_db.get(path)
        assert response.status_code == 403, f"{method.upper()} {path} devrait renvoyer 403 pour un non-admin"


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
        json={"email": "modregcheck@example.com", "username": "modregcheck", "password": "Password123"},
    )
    assert response.status_code == 201


def test_lyrics_public_endpoint_still_works(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, lang_id, _ = _run(_seed(db_session))
    response = client_with_db.get(f"/api/v1/lyrics/song/{song_id}")
    assert response.status_code == 200
    assert response.json()["data"]["available"] is False


def test_favorites_still_works(client_with_db: TestClient, db_session: AsyncSession) -> None:
    song_id, _, _ = _run(_seed(db_session))
    _register(client_with_db, "modfavcheck@example.com", "modfavcheck")
    response = client_with_db.post("/api/v1/favorites", json={"song_id": song_id})
    assert response.status_code == 201
