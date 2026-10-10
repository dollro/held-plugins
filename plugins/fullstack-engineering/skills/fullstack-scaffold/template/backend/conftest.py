import pytest
from allauth.account.models import EmailAddress
from django.core.cache import cache
from rest_framework.test import APIClient

from backend.users.models import User

PASSWORD = "pw-123456-long"


def make_user(email="user@example.com", **extra) -> User:
    user = User.objects.create_user(email=email, password=PASSWORD, **extra)
    EmailAddress.objects.create(user=user, email=email, verified=True, primary=True)
    return user


@pytest.fixture(autouse=True)
def _clear_cache():
    # allauth's rate limits live in the cache; tests must not share them.
    cache.clear()


@pytest.fixture
def user(db):
    return make_user()


@pytest.fixture
def api_client():
    return APIClient(enforce_csrf_checks=True)


@pytest.fixture
def internal_headers(settings):
    settings.INTERNAL_API_SECRET = "test-internal-secret"
    return {"HTTP_X_INTERNAL_SECRET": "test-internal-secret"}


def log_in(client, email, password=PASSWORD):
    """Password login through allauth's login page, like a browser."""
    return client.post("/accounts/login/", {"login": email, "password": password})


def logged_in_as(client) -> str | None:
    response = client.get("/api/v1/auth/me/")
    return response.json()["email"] if response.status_code == 200 else None
