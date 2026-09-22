from __future__ import annotations

from datetime import timedelta

from sqlalchemy import text

from shared.security import create_token


def _headers(account_id) -> dict:
    return {"Authorization": f"Bearer {create_token(str(account_id), 'access', timedelta(minutes=15))}"}


async def test_add_relative_composite_flow_creates_person_links_it_and_appears_in_tree(
    client, db_session, sample_tree
):
    headers = _headers(sample_tree["sunil_account"].id)

    created = await client.post(
        "/api/v1/profiles", json={"first_name": "Kavya", "last_name": "Narayanan"}, headers=headers
    )
    assert created.status_code == 200
    person_id = created.json()["id"]

    row = (
        await db_session.execute(
            text("SELECT user_account_id, created_by_user_account_id FROM person WHERE id = :id"),
            {"id": person_id},
        )
    ).mappings().first()
    assert row["user_account_id"] is None  # unclaimed
    assert str(row["created_by_user_account_id"]) == str(sample_tree["sunil_account"].id)

    linked = await client.post(
        "/api/v1/relationships",
        json={"person_a_id": str(sample_tree["sunil"].id), "person_b_id": person_id, "edge_type": "parent_child"},
        headers=headers,
    )
    assert linked.status_code == 200

    descendants = await client.get(
        "/api/v1/tree/descendants", params={"person_id": str(sample_tree["sunil"].id)}, headers=headers
    )
    assert "Kavya" in {d["first_name"] for d in descendants.json()}


async def test_get_update_and_heritage_round_trip(client, sample_tree):
    headers = _headers(sample_tree["sunil_account"].id)
    person_id = str(sample_tree["deepa"].id)

    fetched = await client.get(f"/api/v1/profiles/{person_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["first_name"] == "Deepa"

    updated = await client.patch(
        f"/api/v1/profiles/{person_id}",
        json={"first_name": "Deepa", "last_name": "Rao", "biography": "Loves painting"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["biography"] == "Loves painting"

    heritage = await client.patch(
        f"/api/v1/profiles/{person_id}/heritage",
        json={"native_country": "India", "native_state": "Tamil Nadu", "native_district": None, "native_village": None},
        headers=headers,
    )
    assert heritage.status_code == 200
    assert heritage.json()["native_country"] == "India"


async def test_get_nonexistent_profile_is_404(client, sample_tree):
    import uuid

    headers = _headers(sample_tree["sunil_account"].id)
    response = await client.get(f"/api/v1/profiles/{uuid.uuid4()}", headers=headers)
    assert response.status_code == 404
