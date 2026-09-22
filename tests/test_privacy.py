from __future__ import annotations

from datetime import timedelta

from shared.security import create_token


def _headers(account_id) -> dict:
    return {"Authorization": f"Bearer {create_token(str(account_id), 'access', timedelta(minutes=15))}"}


async def test_defaults_cover_every_field(client, sample_tree):
    headers = _headers(sample_tree["sunil_account"].id)
    response = await client.get("/api/v1/privacy", headers=headers)
    assert response.status_code == 200
    fields = {s["field_key"] for s in response.json()["settings"]}
    assert fields == {"email", "phone", "date_of_birth", "address", "heritage_info", "biography"}
    assert all(s["visibility"] == "family_network" for s in response.json()["settings"])


async def test_update_only_touches_the_fields_given(client, sample_tree):
    headers = _headers(sample_tree["sunil_account"].id)
    updated = await client.patch(
        "/api/v1/privacy",
        json={"settings": [{"field_key": "phone", "visibility": "private"}]},
        headers=headers,
    )
    assert updated.status_code == 200
    by_field = {s["field_key"]: s["visibility"] for s in updated.json()["settings"]}
    assert by_field["phone"] == "private"
    assert by_field["email"] == "family_network"  # untouched, still the default


async def test_invalid_field_key_is_rejected(client, sample_tree):
    headers = _headers(sample_tree["sunil_account"].id)
    response = await client.patch(
        "/api/v1/privacy",
        json={"settings": [{"field_key": "not_a_real_field", "visibility": "public"}]},
        headers=headers,
    )
    assert response.status_code == 422
