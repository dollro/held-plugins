import pytest

from backend.users.models import ApiKey

pytestmark = pytest.mark.django_db


def post(client, path, payload, headers=None):
    return client.post(path, payload, format="json", **(headers or {}))


def test_internal_endpoint_rejects_missing_secret(api_client, internal_headers):
    response = post(api_client, "/api/v1/internal/validate-key/", {"api_key": "x"})
    assert response.status_code == 403


def test_validate_key(api_client, internal_headers, user):
    _, raw_key = ApiKey.issue(user, "test")
    response = post(
        api_client,
        "/api/v1/internal/validate-key/",
        {"api_key": raw_key},
        internal_headers,
    )
    assert response.json() == {"valid": True, "user_id": user.pk, "email": user.email}


def test_validate_session_of_logged_in_user(client, api_client, internal_headers, user):
    client.force_login(user)
    session_key = client.session.session_key
    response = post(
        api_client,
        "/api/v1/internal/validate-session/",
        {"session_key": session_key},
        internal_headers,
    )
    assert response.json()["user_id"] == user.pk


def test_session_is_invalid_after_logout(client, api_client, internal_headers, user):
    client.force_login(user)
    session_key = client.session.session_key
    client.logout()
    response = post(
        api_client,
        "/api/v1/internal/validate-session/",
        {"session_key": session_key},
        internal_headers,
    )
    assert response.json() == {"valid": False}


def test_unknown_session_is_invalid(api_client, internal_headers):
    response = post(
        api_client,
        "/api/v1/internal/validate-session/",
        {"session_key": "does-not-exist"},
        internal_headers,
    )
    assert response.json() == {"valid": False}
