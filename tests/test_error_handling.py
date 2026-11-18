"""Error handling (GitHub issue #1).

Every error response must be JSON shaped {"message": str, "details": dict}
with an appropriate status code - never Starlette's plain-text
"Internal Server Error", and never leaking SQL, tracebacks or submitted
passwords.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from starlette.requests import Request

from app import app
from shared import error_handlers
from shared.database import get_db
from shared.security import create_token

MISSING_ID = "00000000-0000-0000-0000-000000000001"


def _headers(subject, token_type: str = "access") -> dict:
    return {"Authorization": f"Bearer {create_token(str(subject), token_type, timedelta(minutes=15))}"}


def _assert_error_shape(response, status_code: int) -> dict:
    assert response.status_code == status_code, response.text
    assert response.headers["content-type"].startswith("application/json")
    body = response.json()
    assert set(body) == {"message", "details"}
    assert isinstance(body["message"], str) and body["message"]
    assert isinstance(body["details"], dict)
    return body


@pytest_asyncio.fixture
async def raw_client():
    """Client that returns the 500 response instead of re-raising the server
    exception, so the catch-all handler's output can be asserted on."""
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# --------------------------------------------------------------------------
# Framework errors use the same envelope
# --------------------------------------------------------------------------


async def test_unknown_route_is_json_404(client):
    body = _assert_error_shape(await client.get("/api/v1/does-not-exist"), 404)
    assert body["message"] == "Not Found"


async def test_wrong_method_is_json_405(client):
    _assert_error_shape(await client.delete("/api/v1/auth/login"), 405)


async def test_request_validation_is_json_422_and_does_not_echo_password(client):
    secret = "short1"  # below min_length=8
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "x@example.com", "password": secret, "first_name": "A", "last_name": "B"},
    )
    body = _assert_error_shape(response, 422)
    errors = body["details"]["errors"]
    assert any(e["loc"] == ["body", "password"] for e in errors)
    assert all("input" not in e for e in errors)
    assert secret not in response.text


# --------------------------------------------------------------------------
# Authentication -> 401 with WWW-Authenticate, never 500
# --------------------------------------------------------------------------


async def test_missing_token_is_401(client):
    response = await client.get("/api/v1/users/me")
    _assert_error_shape(response, 401)
    assert response.headers["www-authenticate"] == "Bearer"


async def test_malformed_token_is_401(client):
    response = await client.get("/api/v1/users/me", headers={"Authorization": "Bearer not.a.jwt"})
    _assert_error_shape(response, 401)
    assert response.headers["www-authenticate"] == "Bearer"


async def test_refresh_token_cannot_be_used_as_access_token(client, sample_tree):
    response = await client.get(
        "/api/v1/users/me", headers=_headers(sample_tree["sunil_account"].id, "refresh")
    )
    body = _assert_error_shape(response, 401)
    assert body["message"] == "An access token is required."


async def test_non_uuid_token_subject_is_401_not_500(client):
    response = await client.get("/api/v1/users/me", headers=_headers("not-a-uuid"))
    _assert_error_shape(response, 401)


async def test_refresh_with_non_uuid_subject_is_401_not_500(client):
    refresh = create_token("not-a-uuid", "refresh", timedelta(days=1))
    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    _assert_error_shape(response, 401)


# --------------------------------------------------------------------------
# Relationships
# --------------------------------------------------------------------------


async def test_self_relationship_is_422(client, db_session, sample_tree):
    sunil = sample_tree["sunil"]
    response = await client.post(
        "/api/v1/relationships",
        json={"person_a_id": str(sunil.id), "person_b_id": str(sunil.id)},
        headers=_headers(sample_tree["sunil_account"].id),
    )
    body = _assert_error_shape(response, 422)
    assert "themselves" in body["message"]


async def test_relationship_to_missing_person_is_404(client, db_session, sample_tree):
    sunil = sample_tree["sunil"]
    response = await client.post(
        "/api/v1/relationships",
        json={"person_a_id": str(sunil.id), "person_b_id": MISSING_ID},
        headers=_headers(sample_tree["sunil_account"].id),
    )
    _assert_error_shape(response, 404)
    count = (
        await db_session.execute(
            text("SELECT count(*) FROM relationship_edge WHERE person_b_id = :id"), {"id": MISSING_ID}
        )
    ).scalar_one()
    assert count == 0


async def test_invalid_relationship_source_is_422(client, sample_tree):
    response = await client.post(
        "/api/v1/relationships",
        json={
            "person_a_id": str(sample_tree["sunil"].id),
            "person_b_id": str(sample_tree["deepa"].id),
            "source": "bogus",
        },
        headers=_headers(sample_tree["sunil_account"].id),
    )
    body = _assert_error_shape(response, 422)
    assert body["details"]["errors"][0]["loc"] == ["body", "source"]


async def test_invalid_relationship_status_update_is_422(client, db_session, sample_tree):
    edge_id = (
        await db_session.execute(text("SELECT id FROM relationship_edge LIMIT 1"))
    ).scalar_one()
    response = await client.patch(
        f"/api/v1/relationships/{edge_id}",
        json={"status": "bogus"},
        headers=_headers(sample_tree["sunil_account"].id),
    )
    _assert_error_shape(response, 422)


async def test_duplicate_relationship_is_409(client, db_session, sample_tree, caplog):
    # John -> Sunil parent_child already exists in the sample tree; the
    # uq_edge_pair_type unique index rejects it and the DB error handler
    # maps that to 409 with a generic message.
    # Plain strings captured up front: the rollback below expires the
    # fixture's ORM objects, and lazy-reloading them outside the request
    # would fail under asyncio.
    john_id, sunil_id = str(sample_tree["john"].id), str(sample_tree["sunil"].id)
    with caplog.at_level(logging.INFO, logger="kinverse.api.errors"):
        response = await client.post(
            "/api/v1/relationships",
            json={"person_a_id": john_id, "person_b_id": sunil_id, "edge_type": "parent_child"},
            headers=_headers(sample_tree["sunil_account"].id),
        )
    body = _assert_error_shape(response, 409)
    # Server log identifies the cause by constraint/table, without the row's
    # values (Postgres's DETAIL would echo them - for users, that's an email).
    logged = " ".join(r.getMessage() for r in caplog.records if r.name == "kinverse.api.errors")
    assert "sqlstate=23505" in logged and "table=relationship_edge" in logged
    assert john_id not in logged and sunil_id not in logged
    assert "uq_edge_pair_type" not in response.text  # no constraint/SQL leakage
    assert body["message"] == "A record with these details already exists."

    await db_session.rollback()  # the failed INSERT's savepoint
    count = (
        await db_session.execute(
            text(
                "SELECT count(*) FROM relationship_edge "
                "WHERE person_a_id = :a AND person_b_id = :b AND edge_type = 'parent_child'"
            ),
            {"a": john_id, "b": sunil_id},
        )
    ).scalar_one()
    assert count == 1


# --------------------------------------------------------------------------
# Profiles / invitations / tree
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "payload, field",
    [
        ({"first_name": "A", "last_name": "B", "gender": "bogus"}, "gender"),
        ({"first_name": "A", "last_name": "B", "default_visibility": "everyone"}, "default_visibility"),
        ({"first_name": "A" * 121, "last_name": "B"}, "first_name"),
    ],
)
async def test_invalid_profile_values_are_422(client, sample_tree, payload, field):
    response = await client.post(
        "/api/v1/profiles", json=payload, headers=_headers(sample_tree["sunil_account"].id)
    )
    body = _assert_error_shape(response, 422)
    assert body["details"]["errors"][0]["loc"] == ["body", field]


async def test_invitation_for_missing_person_is_404(client, db_session, sample_tree):
    response = await client.post(
        "/api/v1/invitations/link",
        json={"person_id": MISSING_ID},
        headers=_headers(sample_tree["sunil_account"].id),
    )
    _assert_error_shape(response, 404)
    assert (await db_session.execute(text("SELECT count(*) FROM invitation"))).scalar_one() == 0


@pytest.mark.parametrize(
    "path",
    [
        f"/api/v1/tree/ancestors?person_id={MISSING_ID}",
        f"/api/v1/tree/descendants?person_id={MISSING_ID}",
        f"/api/v1/tree/{MISSING_ID}/siblings",
        f"/api/v1/tree/completeness?person_id={MISSING_ID}",
    ],
)
async def test_tree_queries_for_missing_person_are_404(client, sample_tree, path):
    response = await client.get(path, headers=_headers(sample_tree["sunil_account"].id))
    _assert_error_shape(response, 404)


async def test_tree_queries_for_person_without_relatives_still_200(client, sample_tree):
    # Preserve existing behaviour: a real person with nothing above them is
    # an empty list, not a 404.
    ramesh = sample_tree["ramesh"]
    response = await client.get(
        f"/api/v1/tree/ancestors?person_id={ramesh.id}", headers=_headers(sample_tree["sunil_account"].id)
    )
    assert response.status_code == 200
    assert response.json() == []


# --------------------------------------------------------------------------
# Infrastructure failures
# --------------------------------------------------------------------------


async def test_database_unreachable_is_503(raw_client, sample_tree):
    # Nothing listens on port 1: the connect attempt is refused.
    dead_engine = create_async_engine(
        "postgresql+asyncpg://kinverse:x@127.0.0.1:1/kinverse", connect_args={"timeout": 3}
    )
    dead_sessions = async_sessionmaker(dead_engine)

    async def _dead_db():
        async with dead_sessions() as session:
            yield session

    app.dependency_overrides[get_db] = _dead_db
    try:
        response = await raw_client.get("/api/v1/users/me", headers=_headers(uuid4()))
    finally:
        await dead_engine.dispose()
    body = _assert_error_shape(response, 503)
    assert "temporarily unavailable" in body["message"]
    assert response.headers["retry-after"] == "5"
    assert "127.0.0.1" not in response.text


async def test_unexpected_error_is_json_500_with_error_id(raw_client, caplog):
    async def _broken_db():
        raise RuntimeError("secret internal detail")
        yield  # pragma: no cover - makes this an async generator like get_db

    app.dependency_overrides[get_db] = _broken_db
    with caplog.at_level(logging.ERROR, logger="kinverse.api.errors"):
        response = await raw_client.get("/api/v1/users/me", headers=_headers(uuid4()))

    body = _assert_error_shape(response, 500)
    error_id = body["details"]["error_id"]
    assert len(error_id) == 32
    assert "secret internal detail" not in response.text
    assert "Traceback" not in response.text
    # The same id is in the server log, with the traceback, for support.
    assert any(error_id in rec.getMessage() and rec.exc_info for rec in caplog.records)


# --------------------------------------------------------------------------
# Database-error mapping (the safety net behind the service-level checks)
# --------------------------------------------------------------------------


class _FakePgError(Exception):
    def __init__(self, sqlstate: str, message: str = "") -> None:
        super().__init__(message)
        self.sqlstate = sqlstate


def _request() -> Request:
    return Request({"type": "http", "method": "POST", "path": "/test", "headers": [], "query_string": b""})


@pytest.mark.parametrize(
    "sqlstate, message, expected",
    [
        ("23505", "duplicate key value violates unique constraint", 409),
        ("23503", 'Key (person_id)=(x) is not present in table "person"', 404),
        ("23503", 'Key (id)=(x) is still referenced from table "story"', 409),
        ("23514", "violates check constraint", 422),
        ("23502", "null value in column violates not-null constraint", 422),
        ("99999", "something unforeseen", 500),
    ],
)
async def test_integrity_errors_map_to_status_codes(sqlstate, message, expected):
    exc = IntegrityError("INSERT ...", {}, _FakePgError(sqlstate, message))
    response = await error_handlers._integrity_error(_request(), exc)
    assert response.status_code == expected
    assert b"INSERT" not in response.body
    assert message.encode() not in response.body


async def test_data_error_maps_to_422():
    exc = DataError("INSERT ...", {}, _FakePgError("22P02", "invalid input value for enum"))
    response = await error_handlers._data_error(_request(), exc)
    assert response.status_code == 422
    assert b"enum" not in response.body
