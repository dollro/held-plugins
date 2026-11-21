import pytest
from allauth.account.internal.flows.login import record_authentication
from allauth.socialaccount.models import SocialAccount
from django.test import RequestFactory

from backend.conftest import log_in, logged_in_as, make_user

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff(db):
    return make_user("staff@example.com", is_staff=True)


@pytest.fixture
def linked(db, settings):
    """A company member: created through SSO, later given a password via reset."""
    user = make_user("member@example.com")
    SocialAccount.objects.create(
        user=user, provider=settings.SSO_PROVIDER_ID, uid="sub-1"
    )
    return user


def test_staff_cannot_use_a_password_once_sso_is_configured(client, staff, settings):
    settings.INTERNAL_USERS_SSO_ONLY = True
    log_in(client, staff.email)
    assert logged_in_as(client) is None


def test_provider_linked_users_cannot_use_a_password(client, linked, settings):
    settings.INTERNAL_USERS_SSO_ONLY = True
    log_in(client, linked.email)
    assert logged_in_as(client) is None


def test_external_users_keep_password_login(client, user, settings):
    settings.INTERNAL_USERS_SSO_ONLY = True
    log_in(client, user.email)
    assert logged_in_as(client) == user.email


def test_staff_password_login_works_without_sso(client, staff, settings):
    settings.INTERNAL_USERS_SSO_ONLY = False  # development and end-to-end tests
    log_in(client, staff.email)
    assert logged_in_as(client) == staff.email


def mark_session(client, user, method: str) -> None:
    """Record the login method the way allauth does, bound to this user."""
    request = RequestFactory().get("/")
    request.session = client.session
    record_authentication(request, user, method)
    request.session.save()


def test_sso_sessions_get_mfa_from_the_provider(client, linked, settings):
    settings.MFA_REQUIRED = True
    client.force_login(linked)
    mark_session(client, linked, "socialaccount")
    assert logged_in_as(client) == linked.email


def test_a_password_session_of_a_linked_user_still_needs_mfa(client, linked, settings):
    # The exemption follows how the session authenticated, not the provider link.
    settings.MFA_REQUIRED = True
    client.force_login(linked)
    mark_session(client, linked, "password")
    assert logged_in_as(client) is None
