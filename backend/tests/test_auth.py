"""Tests Phase 2 — Authentication.

Utilise la base SQLite en mémoire (fixtures client_with_db/db_session,
cf. conftest.py) — voir note sur ce choix technique de test dans
conftest.py.
"""

from fastapi.testclient import TestClient

from app.core.security import ACCESS_TOKEN_COOKIE_NAME, decode_access_token

VALID_PAYLOAD = {"email": "jdoe@example.com", "username": "jdoe", "password": "SuperSecret123"}


# ---------------------------------------------------------------- REGISTER


def test_register_valid_creates_user(client_with_db: TestClient) -> None:
    response = client_with_db.post("/api/v1/auth/register", json=VALID_PAYLOAD)
    assert response.status_code == 201
    body = response.json()["data"]
    assert body["email"] == VALID_PAYLOAD["email"]
    assert body["username"] == VALID_PAYLOAD["username"]
    assert body["role"] == "USER"  # role forcé à USER, jamais fourni par le client
    assert body["is_verified"] is False
    assert "id" in body and "created_at" in body


def test_register_never_returns_password_hash_or_password(client_with_db: TestClient) -> None:
    response = client_with_db.post("/api/v1/auth/register", json=VALID_PAYLOAD)
    body = response.json()["data"]
    assert "password" not in body
    assert "password_hash" not in body


def test_register_never_returns_token_in_json_body(client_with_db: TestClient) -> None:
    """Le JWT ne doit jamais apparaître dans le corps JSON (présentes
    instructions Phase 2 §5)."""
    response = client_with_db.post("/api/v1/auth/register", json=VALID_PAYLOAD)
    raw_text = response.text
    assert "access_token" not in raw_text
    assert "token" not in response.json()["data"]


def test_register_sets_httponly_cookie(client_with_db: TestClient) -> None:
    response = client_with_db.post("/api/v1/auth/register", json=VALID_PAYLOAD)
    set_cookie_header = response.headers.get("set-cookie", "")
    assert ACCESS_TOKEN_COOKIE_NAME in set_cookie_header
    assert "httponly" in set_cookie_header.lower()


def test_register_duplicate_email_returns_409(client_with_db: TestClient) -> None:
    client_with_db.post("/api/v1/auth/register", json=VALID_PAYLOAD)
    second = {**VALID_PAYLOAD, "username": "someoneelse"}
    response = client_with_db.post("/api/v1/auth/register", json=second)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EMAIL_ALREADY_EXISTS"


def test_register_duplicate_username_returns_409(client_with_db: TestClient) -> None:
    client_with_db.post("/api/v1/auth/register", json=VALID_PAYLOAD)
    second = {**VALID_PAYLOAD, "email": "other@example.com"}
    response = client_with_db.post("/api/v1/auth/register", json=second)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "USERNAME_ALREADY_EXISTS"


def test_register_invalid_email_returns_422(client_with_db: TestClient) -> None:
    response = client_with_db.post(
        "/api/v1/auth/register", json={**VALID_PAYLOAD, "email": "not-an-email"}
    )
    assert response.status_code == 422


def test_register_short_password_returns_422(client_with_db: TestClient) -> None:
    response = client_with_db.post("/api/v1/auth/register", json={**VALID_PAYLOAD, "password": "short"})
    assert response.status_code == 422


def test_register_password_is_hashed_not_plaintext(db_session, client_with_db: TestClient) -> None:
    import asyncio

    client_with_db.post("/api/v1/auth/register", json=VALID_PAYLOAD)

    async def _fetch() -> str:
        from app.repositories.user_repository import UserRepository

        repo = UserRepository(db_session)
        user = await repo.get_by_email(VALID_PAYLOAD["email"])
        return user.password_hash

    password_hash = asyncio.get_event_loop().run_until_complete(_fetch())
    assert password_hash != VALID_PAYLOAD["password"]
    assert password_hash.startswith("$2b$")  # bcrypt


def test_register_client_cannot_set_role(client_with_db: TestClient) -> None:
    """Le schéma d'entrée n'accepte pas 'role' — champ ignoré/rejeté."""
    payload = {**VALID_PAYLOAD, "role": "ADMIN"}
    response = client_with_db.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    assert response.json()["data"]["role"] == "USER"


# ------------------------------------------------------------------ LOGIN


def test_login_valid_returns_user_and_sets_cookie(client_with_db: TestClient) -> None:
    client_with_db.post("/api/v1/auth/register", json=VALID_PAYLOAD)
    response = client_with_db.post(
        "/api/v1/auth/login", json={"email": VALID_PAYLOAD["email"], "password": VALID_PAYLOAD["password"]}
    )
    assert response.status_code == 200
    assert response.json()["data"]["email"] == VALID_PAYLOAD["email"]
    assert ACCESS_TOKEN_COOKIE_NAME in response.headers.get("set-cookie", "")


def test_login_wrong_password_returns_401_generic_message(client_with_db: TestClient) -> None:
    client_with_db.post("/api/v1/auth/register", json=VALID_PAYLOAD)
    response = client_with_db.post(
        "/api/v1/auth/login", json={"email": VALID_PAYLOAD["email"], "password": "WrongPassword1"}
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_unknown_email_returns_same_generic_message_as_wrong_password(
    client_with_db: TestClient,
) -> None:
    """Anti-énumération : même code/message pour email inconnu et mot de
    passe incorrect (Livrable 3 §2.2)."""
    response = client_with_db.post(
        "/api/v1/auth/login", json={"email": "unknown@example.com", "password": "whatever123"}
    )
    assert response.status_code == 401
    body = response.json()["error"]
    assert body["code"] == "INVALID_CREDENTIALS"

    client_with_db.post("/api/v1/auth/register", json=VALID_PAYLOAD)
    wrong_pw_response = client_with_db.post(
        "/api/v1/auth/login", json={"email": VALID_PAYLOAD["email"], "password": "WrongPassword1"}
    )
    assert wrong_pw_response.json()["error"]["message"] == body["message"]


def test_login_disabled_account_returns_403(client_with_db: TestClient, db_session) -> None:
    import asyncio

    client_with_db.post("/api/v1/auth/register", json=VALID_PAYLOAD)

    async def _disable() -> None:
        from app.repositories.user_repository import UserRepository

        repo = UserRepository(db_session)
        user = await repo.get_by_email(VALID_PAYLOAD["email"])
        user.is_active = False
        await db_session.commit()

    asyncio.get_event_loop().run_until_complete(_disable())

    response = client_with_db.post(
        "/api/v1/auth/login", json={"email": VALID_PAYLOAD["email"], "password": VALID_PAYLOAD["password"]}
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACCOUNT_DISABLED"


def test_login_never_returns_token_in_json_body(client_with_db: TestClient) -> None:
    client_with_db.post("/api/v1/auth/register", json=VALID_PAYLOAD)
    response = client_with_db.post(
        "/api/v1/auth/login", json={"email": VALID_PAYLOAD["email"], "password": VALID_PAYLOAD["password"]}
    )
    assert "token" not in response.json()["data"]


# ----------------------------------------------------------------- LOGOUT


def test_logout_clears_cookie(client_with_db: TestClient) -> None:
    client_with_db.post("/api/v1/auth/register", json=VALID_PAYLOAD)
    response = client_with_db.post("/api/v1/auth/logout")
    assert response.status_code == 204
    set_cookie_header = response.headers.get("set-cookie", "")
    # Un cookie supprimé est renvoyé avec une expiration passée / valeur vide.
    assert ACCESS_TOKEN_COOKIE_NAME in set_cookie_header


def test_logout_is_idempotent_without_prior_session(client_with_db: TestClient) -> None:
    response = client_with_db.post("/api/v1/auth/logout")
    assert response.status_code == 204


# -------------------------------------------------------------------- ME


def test_me_authenticated_returns_current_user(client_with_db: TestClient) -> None:
    client_with_db.cookies.clear()
    client_with_db.post("/api/v1/auth/register", json=VALID_PAYLOAD)
    response = client_with_db.get("/api/v1/auth/me")
    assert response.status_code == 200
    assert response.json()["data"]["email"] == VALID_PAYLOAD["email"]


def test_me_without_cookie_returns_401(client_with_db: TestClient) -> None:
    response = client_with_db.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_me_invalid_token_returns_401(client_with_db: TestClient) -> None:
    client_with_db.cookies.set(ACCESS_TOKEN_COOKIE_NAME, "not-a-valid-jwt")
    response = client_with_db.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_expired_token_returns_401(client_with_db: TestClient) -> None:
    from datetime import UTC, datetime, timedelta

    from jose import jwt

    from app.core.config import get_settings

    settings = get_settings()
    expired_token = jwt.encode(
        {"sub": "00000000-0000-0000-0000-000000000000", "exp": datetime.now(UTC) - timedelta(minutes=1)},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    client_with_db.cookies.set(ACCESS_TOKEN_COOKIE_NAME, expired_token)
    response = client_with_db.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_deleted_user_returns_401(client_with_db: TestClient, db_session) -> None:
    import asyncio
    from datetime import UTC, datetime

    client_with_db.cookies.clear()
    client_with_db.post("/api/v1/auth/register", json=VALID_PAYLOAD)

    async def _soft_delete() -> None:
        from app.repositories.user_repository import UserRepository

        repo = UserRepository(db_session)
        user = await repo.get_by_email(VALID_PAYLOAD["email"])
        user.deleted_at = datetime.now(UTC)
        await db_session.commit()

    asyncio.get_event_loop().run_until_complete(_soft_delete())

    response = client_with_db.get("/api/v1/auth/me")
    assert response.status_code == 401


# --------------------------------------------------------------- SECURITY


def test_password_never_appears_in_any_response(client_with_db: TestClient) -> None:
    client_with_db.cookies.clear()
    r1 = client_with_db.post("/api/v1/auth/register", json=VALID_PAYLOAD)
    r2 = client_with_db.post(
        "/api/v1/auth/login", json={"email": VALID_PAYLOAD["email"], "password": VALID_PAYLOAD["password"]}
    )
    r3 = client_with_db.get("/api/v1/auth/me")
    for response in (r1, r2, r3):
        assert VALID_PAYLOAD["password"] not in response.text
        assert "password_hash" not in response.text


def test_decode_access_token_round_trip() -> None:
    from app.core.security import create_access_token

    token = create_access_token(subject="some-user-id")
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "some-user-id"


def test_decode_access_token_rejects_tampered_token() -> None:
    from app.core.security import create_access_token

    token = create_access_token(subject="some-user-id")
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    assert decode_access_token(tampered) is None
