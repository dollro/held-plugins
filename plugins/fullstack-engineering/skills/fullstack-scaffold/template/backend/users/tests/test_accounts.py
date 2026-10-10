import re

import pytest
from allauth.mfa.totp.internal.auth import TOTP, generate_totp_secret
from django.core import mail

from backend.conftest import PASSWORD, log_in, logged_in_as

pytestmark = pytest.mark.django_db

NEW = {"email": "new@example.com", "password1": PASSWORD, "password2": PASSWORD}


def test_closed_signup_creates_no_account(client, settings, django_user_model):
    settings.SIGNUP_OPEN = False
    client.post("/accounts/signup/", NEW)
    assert not django_user_model.objects.filter(email=NEW["email"]).exists()
    assert not mail.outbox


def test_signup_requires_the_emailed_code(client, settings):
    settings.SIGNUP_OPEN = True
    client.post("/accounts/signup/", NEW)
    assert logged_in_as(client) is None  # not before the address is verified

    # The code sits on its own line; its format (length, dashes) is allauth's choice.
    code = re.search(
        r"^\s*([A-Z0-9][A-Z0-9-]{4,}[A-Z0-9])\s*$", mail.outbox[0].body, re.M
    )[1]
    client.post("/accounts/confirm-email/", {"code": code})
    assert logged_in_as(client) == NEW["email"]


def test_unverified_users_cannot_log_in(client, django_user_model):
    django_user_model.objects.create_user(
        email="unverified@example.com", password=PASSWORD
    )
    log_in(client, "unverified@example.com")
    assert logged_in_as(client) is None


def test_login_asks_for_the_second_factor_once_set_up(client, user):
    TOTP.activate(user, generate_totp_secret())  # internal helper, fine for a test
    response = log_in(client, user.email)
    assert response["Location"].startswith("/accounts/2fa/authenticate/")
    assert logged_in_as(client) is None


def test_mfa_required_still_allows_logout(client, user, settings):
    settings.MFA_REQUIRED = True
    client.force_login(user)
    assert client.post("/api/v1/auth/logout/").status_code == 204


def test_mfa_required_sends_users_to_the_setup_first(client, user, settings):
    settings.MFA_REQUIRED = True
    client.force_login(user)
    assert client.get("/app/")["Location"] == "/accounts/2fa/"
    response = client.get("/api/v1/auth/me/")
    assert response.status_code == 403
    assert "multi-factor" in response.json()["detail"]
    assert client.get("/api/v1/health/").status_code == 200


def test_mfa_required_also_applies_to_the_realtime_service(
    client, user, settings, internal_headers
):
    settings.MFA_REQUIRED = True
    client.force_login(user)
    response = client.post(
        "/api/v1/internal/validate-session/",
        {"session_key": client.session.session_key},
        content_type="application/json",
        **internal_headers,
    )
    assert response.json() == {"valid": False}


def test_users_with_mfa_pass_the_requirement(client, user, settings):
    settings.MFA_REQUIRED = True
    TOTP.activate(user, generate_totp_secret())
    client.force_login(user)
    assert logged_in_as(client) == user.email
