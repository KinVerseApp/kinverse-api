from __future__ import annotations

from datetime import timedelta

from sqlalchemy import text

from shared.security import create_token


def _headers(account_id) -> dict:
    return {"Authorization": f"Bearer {create_token(str(account_id), 'access', timedelta(minutes=15))}"}


async def _seed_notification(db_session, account_id, type_="birthday", is_read=False):
    await db_session.execute(
        text(
            "INSERT INTO notification (recipient_user_account_id, type, payload, is_read) "
            "VALUES (:account_id, :type, '{}', :is_read)"
        ),
        {"account_id": str(account_id), "type": type_, "is_read": is_read},
    )
    await db_session.commit()


async def test_list_and_unread_count(client, db_session, sample_tree):
    await _seed_notification(db_session, sample_tree["sunil_account"].id, "birthday")
    await _seed_notification(db_session, sample_tree["sunil_account"].id, "invite_accepted")
    headers = _headers(sample_tree["sunil_account"].id)

    listed = await client.get("/api/v1/notifications", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 2

    unread = await client.get("/api/v1/notifications/unread-count", headers=headers)
    assert unread.json() == {"count": 2}


async def test_a_different_user_cannot_mark_someone_elses_notification_read(client, db_session, sample_tree):
    await _seed_notification(db_session, sample_tree["sunil_account"].id, "birthday")
    notif_id = (
        await db_session.execute(
            text("SELECT id FROM notification WHERE recipient_user_account_id = :id"),
            {"id": str(sample_tree["sunil_account"].id)},
        )
    ).scalar_one()

    other_id = (
        await db_session.execute(
            text(
                "INSERT INTO user_account (email, auth_provider, status) "
                "VALUES ('intruder@example.com', 'email', 'active') RETURNING id"
            )
        )
    ).scalar_one()
    await db_session.commit()

    denied = await client.patch(f"/api/v1/notifications/{notif_id}/read", headers=_headers(other_id))
    assert denied.status_code == 403

    allowed = await client.patch(
        f"/api/v1/notifications/{notif_id}/read", headers=_headers(sample_tree["sunil_account"].id)
    )
    assert allowed.status_code == 200
    assert allowed.json()["is_read"] is True


async def test_mark_all_read(client, db_session, sample_tree):
    await _seed_notification(db_session, sample_tree["sunil_account"].id, "birthday")
    await _seed_notification(db_session, sample_tree["sunil_account"].id, "new_family_member")
    headers = _headers(sample_tree["sunil_account"].id)

    response = await client.patch("/api/v1/notifications/read-all", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"updated_count": 2}

    unread = await client.get("/api/v1/notifications/unread-count", headers=headers)
    assert unread.json() == {"count": 0}
