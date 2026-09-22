from __future__ import annotations

from datetime import timedelta

from sqlalchemy import text

from shared.security import create_token, verify_password


async def test_register_creates_account_and_person_with_hashed_password(client, db_session):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "nina.test@example.com", "password": "correct-horse-battery",
            "first_name": "Nina", "last_name": "Testson",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body and "refresh_token" in body

    row = (
        await db_session.execute(
            text("SELECT id, password_hash FROM user_account WHERE email = 'nina.test@example.com'")
        )
    ).mappings().first()
    assert row is not None
    assert row["password_hash"] is not None
    assert verify_password("correct-horse-battery", row["password_hash"])

    person = (
        await db_session.execute(
            text("SELECT first_name, last_name FROM person WHERE user_account_id = :id"),
            {"id": row["id"]},
        )
    ).mappings().first()
    assert person == {"first_name": "Nina", "last_name": "Testson"}

    # The returned token's subject must be the real account id, not the
    # email - every authenticated endpoint depends on this.
    me = await client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {body['access_token']}"}
    )
    assert me.status_code == 200
    assert me.json()["id"] == str(row["id"])


async def test_duplicate_registration_is_rejected(client):
    payload = {
        "email": "dup.test@example.com", "password": "whatever12345",
        "first_name": "A", "last_name": "B",
    }
    first = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 200
    second = await client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 401


async def test_login_wrong_password_and_nonexistent_email_give_identical_response(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "login.test@example.com", "password": "the-real-password",
            "first_name": "Lo", "last_name": "Gin",
        },
    )

    wrong_password = await client.post(
        "/api/v1/auth/login", json={"email": "login.test@example.com", "password": "not-it-at-all"}
    )
    nonexistent = await client.post(
        "/api/v1/auth/login", json={"email": "nobody.here@example.com", "password": "not-it-at-all"}
    )

    assert wrong_password.status_code == nonexistent.status_code == 401
    # Same message for both - otherwise the error itself confirms which
    # emails are registered (account enumeration).
    assert wrong_password.json() == nonexistent.json()


async def test_login_correct_password_succeeds(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "correct.test@example.com", "password": "the-real-password",
            "first_name": "Cor", "last_name": "Rect",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "correct.test@example.com", "password": "the-real-password"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_refresh_rejects_a_token_it_never_issued(client):
    # This is the regression test for the actual security hole found in
    # review: refresh_token() used to sign and return valid credentials for
    # ANY string at all, without checking it. This must now fail.
    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": "not-a-real-token"})
    assert response.status_code == 401


async def test_refresh_rejects_an_access_token_used_as_a_refresh_token(client, sample_tree):
    access_token = create_token(str(sample_tree["sunil_account"].id), "access", timedelta(minutes=15))
    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})
    assert response.status_code == 401


async def test_refresh_with_a_genuine_refresh_token_succeeds(client, sample_tree):
    refresh = create_token(str(sample_tree["sunil_account"].id), "refresh", timedelta(days=30))
    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert response.status_code == 200
    assert "access_token" in response.json()
