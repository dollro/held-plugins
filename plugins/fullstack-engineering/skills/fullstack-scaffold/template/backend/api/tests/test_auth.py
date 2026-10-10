import pytest

from backend.conftest import log_in, logged_in_as

pytestmark = pytest.mark.django_db


def test_health_is_public(api_client):
    response = api_client.get("/api/v1/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_me_requires_authentication(api_client):
    assert api_client.get("/api/v1/auth/me/").status_code == 403


def test_password_login_through_allauth(client, user):
    log_in(client, user.email)
    assert logged_in_as(client) == user.email


def test_wrong_password_is_refused(client, user):
    log_in(client, user.email, "wrong-password")
    assert logged_in_as(client) is None


def test_there_is_no_login_endpoint_besides_allauth(api_client):
    # A JSON login would bypass allauth's rate limits, verification and MFA.
    assert api_client.post("/api/v1/auth/login/").status_code == 404


def test_admin_login_goes_through_allauth(client):
    response = client.get("/admin/login/")
    assert response.status_code == 302
    assert response["Location"].startswith("/accounts/login/")


def test_logout_requires_csrf(api_client, user):
    api_client.force_login(user)
    assert api_client.post("/api/v1/auth/logout/").status_code == 403
# >>> internal


def test_local_login_can_be_disabled(client, user, settings):
    settings.SOCIALACCOUNT_ONLY = True  # what LOCAL_LOGIN_ENABLED=False sets
    log_in(client, user.email)
    assert logged_in_as(client) is None


def test_nobody_signs_up_with_a_password(client, db):
    client.post(
        "/accounts/signup/",
        {
            "email": "new@example.com",
            "password1": "x-Long-pw-1",
            "password2": "x-Long-pw-1",
        },
    )
    assert logged_in_as(client) is None
# <<< internal


def test_test_event_is_enqueued_after_commit(
    api_client, user, monkeypatch, django_capture_on_commit_callbacks
):
    sent = []
    monkeypatch.setattr("backend.api.views.send_test_event.delay", sent.append)
    api_client.force_authenticate(user)
    with django_capture_on_commit_callbacks(execute=True):
        response = api_client.post("/api/v1/events/test/", HTTP_X_CSRFTOKEN="x")
    assert response.status_code == 202
    assert sent == [user.pk]
