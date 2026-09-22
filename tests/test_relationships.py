from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import text

from shared.security import create_token


def _auth_headers(user_id) -> dict:
    token = create_token(str(user_id), "access", timedelta(minutes=15))
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_add_relative_creates_confirmed_edge(client, db_session, sample_tree):
    sunil = sample_tree["sunil"]
    deepa = sample_tree["deepa"]
    headers = _auth_headers(sample_tree["sunil_account"].id)

    response = await client.post(
        "/api/v1/relationships",
        json={"person_a_id": str(sunil.id), "person_b_id": str(deepa.id), "edge_type": "parent_child"},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "confirmed"  # manual adds auto-confirm - no one else to confirm against

    # Validate against the database directly, not just the API response -
    # the row actually has to be there with the right values.
    row = (
        await db_session.execute(
            text("SELECT edge_type, status, source FROM relationship_edge WHERE id = :id"),
            {"id": body["id"]},
        )
    ).mappings().first()
    assert row is not None
    assert row["edge_type"] == "parent_child"
    assert row["status"] == "confirmed"
    assert row["source"] == "manual"


@pytest.mark.asyncio
async def test_partner_edge_canonical_ordering_is_enforced(client, db_session, sample_tree):
    # person_a/person_b given in the "wrong" (larger-uuid-first) order on
    # purpose - the service must swap them to satisfy the DB's
    # chk_partner_canonical_order constraint, not just happen to work when
    # the caller already orders them correctly.
    a, b = sample_tree["sunil"], sample_tree["deepa"]
    larger, smaller = (a, b) if str(a.id) > str(b.id) else (b, a)
    headers = _auth_headers(sample_tree["sunil_account"].id)

    response = await client.post(
        "/api/v1/relationships",
        json={
            "person_a_id": str(larger.id), "person_b_id": str(smaller.id),
            "edge_type": "partner", "partner_type": "partner",
        },
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["person_a_id"] == str(smaller.id)
    assert body["person_b_id"] == str(larger.id)

    count = (
        await db_session.execute(
            text(
                "SELECT count(*) FROM relationship_edge "
                "WHERE edge_type = 'partner' AND person_a_id = :a AND person_b_id = :b"
            ),
            {"a": str(smaller.id), "b": str(larger.id)},
        )
    ).scalar_one()
    assert count == 1


@pytest.mark.asyncio
async def test_partner_edge_without_partner_type_is_rejected(client, sample_tree):
    headers = _auth_headers(sample_tree["sunil_account"].id)
    response = await client.post(
        "/api/v1/relationships",
        json={
            "person_a_id": str(sample_tree["sunil"].id),
            "person_b_id": str(sample_tree["deepa"].id),
            "edge_type": "partner",
        },
        headers=headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_confirm_reject_remove_lifecycle(client, db_session, sample_tree):
    headers = _auth_headers(sample_tree["sunil_account"].id)
    create = await client.post(
        "/api/v1/relationships",
        json={
            "person_a_id": str(sample_tree["sunil"].id), "person_b_id": str(sample_tree["kiran"].id),
            "edge_type": "parent_child", "source": "search_match",
        },
        headers=headers,
    )
    rel_id = create.json()["id"]
    assert create.json()["status"] == "pending"  # search_match starts pending, not auto-confirmed

    confirmed = await client.post(f"/api/v1/relationships/{rel_id}/confirm", headers=headers)
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "confirmed"

    row = (
        await db_session.execute(
            text("SELECT confirmed_at FROM relationship_edge WHERE id = :id"), {"id": rel_id}
        )
    ).mappings().first()
    assert row["confirmed_at"] is not None

    deleted = await client.delete(f"/api/v1/relationships/{rel_id}", headers=headers)
    assert deleted.status_code == 204

    row = (
        await db_session.execute(
            text("SELECT count(*) FROM relationship_edge WHERE id = :id"), {"id": rel_id}
        )
    ).scalar_one()
    assert row == 0


@pytest.mark.asyncio
async def test_confirming_nonexistent_relationship_is_404(client, sample_tree):
    import uuid

    headers = _auth_headers(sample_tree["sunil_account"].id)
    response = await client.post(f"/api/v1/relationships/{uuid.uuid4()}/confirm", headers=headers)
    assert response.status_code == 404
