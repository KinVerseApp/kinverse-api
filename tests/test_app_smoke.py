from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def test_openapi_contains_expected_sections() -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    assert spec["info"]["title"] == "KinVerse API"
    assert any(tag["name"] == "auth" for tag in spec["tags"])
    assert any(tag["name"] == "tree" for tag in spec["tags"])


def test_root_redirects_to_docs() -> None:
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (200, 307, 302)
