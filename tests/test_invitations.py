from __future__ import annotations

from datetime import timedelta

from sqlalchemy import text

from shared.security import create_token


def _headers(account_id) -> dict:
    return {"Authorization": f"Bearer {create_token(str(account_id), 'access', timedelta(minutes=15))}"}


async def test_full_invitation_lifecycle_claims_the_person_on_accept(client, db_session, sample_tree):
    sunil_headers = _headers(sample_tree["sunil_account"].id)

    created = await client.post(
        "/api/v1/profiles", json={"first_name": "Kavya", "last_name": "Narayanan"}, headers=sunil_headers
    )
    person_id = created.json()["id"]
    await client.post(
        "/api/v1/relationships",
        json={"person_a_id": str(sample_tree["sunil"].id), "person_b_id": person_id, "edge_type": "parent_child"},
        headers=sunil_headers,
    )

    invited = await client.post(
        "/api/v1/invitations/sms",
        json={"invitee_phone": "+15551234567", "person_id": person_id},
        headers=sunil_headers,
    )
    assert invited.status_code == 200
    assert invited.json()["invite_code"].startswith("KIN-")
    assert invited.json()["status"] == "sent"
    invite_id = invited.json()["id"]

    # A genuinely different account accepts it
    other_account_id = (
        await db_session.execute(
            text(
                "INSERT INTO user_account (email, auth_provider, status) "
                "VALUES ('kavya.claims@example.com', 'email', 'active') RETURNING id"
            )
        )
    ).scalar_one()
    await db_session.commit()

    accepted = await client.post(
        f"/api/v1/invitations/{invite_id}/accept", headers=_headers(other_account_id)
    )
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "accepted"

    row = (
        await db_session.execute(
            text("SELECT user_account_id FROM person WHERE id = :id"), {"id": person_id}
        )
    ).mappings().first()
    assert str(row["user_account_id"]) == str(other_account_id)


async def test_invalid_method_is_rejected(client, sample_tree):
    headers = _headers(sample_tree["sunil_account"].id)
    response = await client.post("/api/v1/invitations", json={"method": "carrier_pigeon"}, headers=headers)
    assert response.status_code == 422


async def test_decline_invitation(client, sample_tree):
    headers = _headers(sample_tree["sunil_account"].id)
    created = await client.post(
        "/api/v1/invitations/email", json={"invitee_email": "someone@example.com"}, headers=headers
    )
    invite_id = created.json()["id"]
    declined = await client.post(f"/api/v1/invitations/{invite_id}/decline", headers=headers)
    assert declined.status_code == 200
    assert declined.json()["status"] == "declined"
