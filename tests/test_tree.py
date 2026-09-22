from __future__ import annotations

from datetime import timedelta

from shared.security import create_token


def _headers(account_id) -> dict:
    return {"Authorization": f"Bearer {create_token(str(account_id), 'access', timedelta(minutes=15))}"}


async def test_get_tree_defaults_to_the_caller_own_person(client, sample_tree):
    response = await client.get("/api/v1/tree", headers=_headers(sample_tree["sunil_account"].id))
    assert response.status_code == 200
    body = response.json()
    assert body["root_id"] == str(sample_tree["sunil"].id)
    names = {(n["first_name"], n["relationship"]) for n in body["nodes"]}
    assert ("John", "parent") in names
    assert ("Mary", "parent") in names
    assert ("Ramesh", "grandparent") in names
    assert ("Lakshmi", "grandparent") in names
    assert ("Priya", "spouse") in names


async def test_ancestors_and_descendants_have_correct_depth_labels(client, sample_tree):
    headers = _headers(sample_tree["sunil_account"].id)
    person_id = str(sample_tree["sunil"].id)

    ancestors = await client.get("/api/v1/tree/ancestors", params={"person_id": person_id}, headers=headers)
    assert ancestors.status_code == 200
    by_name = {a["first_name"]: a["relationship"] for a in ancestors.json()}
    assert by_name == {"John": "parent", "Mary": "parent", "Ramesh": "grandparent", "Lakshmi": "grandparent"}

    descendants = await client.get(
        "/api/v1/tree/descendants", params={"person_id": person_id}, headers=headers
    )
    assert descendants.status_code == 200
    by_name = {d["first_name"]: d["relationship"] for d in descendants.json()}
    assert by_name == {"Arjun": "child", "Meera": "child"}


async def test_siblings_distinguishes_full_from_half(client, sample_tree):
    headers = _headers(sample_tree["sunil_account"].id)

    arjun_siblings = await client.get(
        "/api/v1/tree/{}/siblings".format(sample_tree["arjun"].id), headers=headers
    )
    assert arjun_siblings.status_code == 200
    assert [s["first_name"] for s in arjun_siblings.json()] == ["Meera"]
    assert arjun_siblings.json()[0]["relationship"] == "full_sibling"

    sunil_siblings = await client.get(
        "/api/v1/tree/{}/siblings".format(sample_tree["sunil"].id), headers=headers
    )
    assert sunil_siblings.json() == []  # Sunil genuinely has none in the sample tree


async def test_completeness_score_reflects_what_is_actually_missing(client, sample_tree):
    headers = _headers(sample_tree["sunil_account"].id)
    response = await client.get(
        "/api/v1/tree/completeness", params={"person_id": str(sample_tree["sunil"].id)}, headers=headers
    )
    assert response.status_code == 200
    body = response.json()
    # Sunil has: a parent, a spouse, a child. He has no sibling in the
    # sample tree - that's the one thing the score should be missing.
    assert body["score"] == 0.75
    assert "sibling" not in body["coverage"]
    assert "parent" in body["coverage"] and "spouse" in body["coverage"] and "child" in body["coverage"]
