from __future__ import annotations

from datetime import timedelta

from shared.security import create_token


def _headers(account_id) -> dict:
    return {"Authorization": f"Bearer {create_token(str(account_id), 'access', timedelta(minutes=15))}"}


async def test_exact_name_match(client, sample_tree):
    headers = _headers(sample_tree["sunil_account"].id)
    response = await client.get("/api/v1/search/name", params={"q": "Deepa Rao"}, headers=headers)
    assert response.status_code == 200
    assert response.json()[0]["first_name"] == "Deepa"
    assert response.json()[0]["match_score"] == 1.0


async def test_typo_tolerant_match(client, sample_tree):
    # This is the actual point of using pg_trgm instead of LIKE '%...%'.
    headers = _headers(sample_tree["sunil_account"].id)
    response = await client.get("/api/v1/search/name", params={"q": "Deepe Roa"}, headers=headers)
    assert response.status_code == 200
    assert response.json()[0]["first_name"] == "Deepa"
    assert 0 < response.json()[0]["match_score"] < 1.0


async def test_no_match_returns_empty_not_an_error(client, sample_tree):
    headers = _headers(sample_tree["sunil_account"].id)
    response = await client.get("/api/v1/search/name", params={"q": "Zzyxx Qwerty"}, headers=headers)
    assert response.status_code == 200
    assert response.json() == []


async def test_too_short_query_is_rejected(client, sample_tree):
    headers = _headers(sample_tree["sunil_account"].id)
    response = await client.get("/api/v1/search/name", params={"q": "D"}, headers=headers)
    assert response.status_code == 422
