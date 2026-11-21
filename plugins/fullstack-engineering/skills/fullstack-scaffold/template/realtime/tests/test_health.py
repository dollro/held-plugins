from realtime.config import Settings


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_version_is_the_release_tag_else_the_commit(monkeypatch):
    """The deploy sets APP_VERSION from the tag; the image only knows its commit."""
    monkeypatch.setenv("GIT_SHA", "0123456789abcdef0123")
    monkeypatch.delenv("APP_VERSION", raising=False)
    assert Settings().version == "dev-0123456789ab"
    monkeypatch.setenv("APP_VERSION", "__VERSION_EXAMPLE__")
    assert Settings().version == "__VERSION_EXAMPLE__"
