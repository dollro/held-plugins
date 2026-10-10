import pytest
from starlette.requests import Request

from realtime import auth
from realtime.django_client import AuthUnavailable


def make_request(headers: dict[str, str]) -> Request:
    raw = [(k.lower().encode(), v.encode()) for k, v in headers.items()]
    return Request(
        {"type": "http", "scheme": "http", "headers": raw, "path": "/v1/events"}
    )


@pytest.mark.parametrize(
    ("headers", "cross_site"),
    [
        ({"sec-fetch-site": "same-origin"}, False),
        ({"sec-fetch-site": "cross-site"}, True),
        ({"sec-fetch-site": "same-site"}, True),
        ({"origin": "http://app.test", "host": "app.test"}, False),
        ({"origin": "https://evil.test", "host": "app.test"}, True),
        # Plain-HTTP non-localhost origins get no Fetch Metadata; same-origin GETs no Origin.
        ({"host": "app.test"}, False),
    ],
)
def test_cross_site_detection(headers, cross_site):
    assert auth.is_cross_site(make_request(headers)) is cross_site


def test_events_without_credentials_is_401(client):
    assert client.get("/v1/events").status_code == 401


def test_cross_site_cookie_request_is_refused(client):
    client.cookies.set("sessionid", "any")
    response = client.get("/v1/events", headers={"sec-fetch-site": "cross-site"})
    assert response.status_code == 403


def test_foreign_origin_is_refused(client):
    client.cookies.set("sessionid", "any")
    response = client.get("/v1/events", headers={"origin": "https://evil.test"})
    assert response.status_code == 403


def test_invalid_session_is_401(client, monkeypatch):
    async def reject(session_key):
        return None

    monkeypatch.setattr(auth, "validate_session", reject)
    client.cookies.set("sessionid", "bad")
    assert client.get("/v1/events").status_code == 401


def test_fail_closed_when_django_is_down(client, monkeypatch):
    async def unavailable(session_key):
        raise AuthUnavailable

    monkeypatch.setattr(auth, "validate_session", unavailable)
    client.cookies.set("sessionid", "any")
    assert client.get("/v1/events").status_code == 503


def test_sse_formatting():
    from realtime.routers.events import sse

    assert sse('{"a": 1}', event="ready") == 'event: ready\ndata: {"a": 1}\n\n'
