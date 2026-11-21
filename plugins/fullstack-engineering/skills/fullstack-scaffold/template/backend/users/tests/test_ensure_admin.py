"""ensure_admin: the admin account follows the env on every deploy and start."""

import pytest
from allauth.account.models import EmailAddress
from django.core.management import call_command
from django.core.management.base import CommandError

from backend.users.models import User

pytestmark = pytest.mark.django_db

ADMIN = "admin@example.com"
PASSWORD = "Env-admin-pass-4821"


@pytest.fixture
def admin_env(monkeypatch):
    monkeypatch.setenv("DJANGO_SUPERUSER_EMAIL", ADMIN)
    monkeypatch.delenv("DJANGO_SUPERUSER_USERNAME", raising=False)
    monkeypatch.delenv("DJANGO_SUPERUSER_PASSWORD", raising=False)
    return monkeypatch


def admin() -> User:
    return User.objects.get(email=ADMIN)


def test_email_is_required(monkeypatch):
    monkeypatch.delenv("DJANGO_SUPERUSER_EMAIL", raising=False)
    with pytest.raises(CommandError, match="DJANGO_SUPERUSER_EMAIL"):
        call_command("ensure_admin")


def test_without_password_the_new_admin_has_an_unusable_one(admin_env):
    call_command("ensure_admin")

    user = admin()
    assert user.is_superuser and user.is_staff and user.is_active
    assert not user.has_usable_password()
    address = EmailAddress.objects.get(user=user)
    assert (address.email, address.verified, address.primary) == (ADMIN, True, True)


def test_without_password_an_existing_password_is_left_alone(admin_env):
    call_command("ensure_admin")
    user = admin()
    user.set_password("set-by-the-owner-1")
    user.save()

    call_command("ensure_admin")

    assert admin().check_password("set-by-the-owner-1")
    assert User.objects.filter(email=ADMIN).count() == 1


def test_a_new_admin_gets_the_env_password_which_is_never_printed(admin_env, capsys):
    admin_env.setenv("DJANGO_SUPERUSER_PASSWORD", PASSWORD)

    call_command("ensure_admin")

    assert admin().is_superuser and admin().check_password(PASSWORD)
    assert PASSWORD not in capsys.readouterr().out


def test_a_changed_env_password_replaces_the_admins_password(admin_env):
    call_command("ensure_admin")
    user = admin()
    user.set_password("set-by-the-owner-1")
    user.save()
    admin_env.setenv("DJANGO_SUPERUSER_PASSWORD", PASSWORD)

    call_command("ensure_admin")

    assert admin().check_password(PASSWORD)


def test_an_unchanged_env_password_keeps_the_hash(admin_env):
    """No new hash on every deploy or start, so the admin's sessions survive."""
    admin_env.setenv("DJANGO_SUPERUSER_PASSWORD", PASSWORD)
    call_command("ensure_admin")
    before = admin().password

    call_command("ensure_admin")

    assert admin().password == before


def test_a_weak_password_is_refused_without_creating_the_admin(admin_env):
    admin_env.setenv("DJANGO_SUPERUSER_PASSWORD", "123")

    with pytest.raises(CommandError, match="too weak"):
        call_command("ensure_admin")

    assert not User.objects.filter(email=ADMIN).exists()


def test_an_existing_non_admin_is_never_promoted(admin_env):
    User.objects.create_user(email=ADMIN, password="pw-123456-long")
    admin_env.setenv("DJANGO_SUPERUSER_PASSWORD", PASSWORD)

    with pytest.raises(CommandError, match="not an admin"):
        call_command("ensure_admin")

    user = admin()
    assert not user.is_superuser and not user.check_password(PASSWORD)


def test_a_username_of_another_account_is_a_clear_error(admin_env):
    admin_env.setenv("DJANGO_SUPERUSER_USERNAME", "admin")
    User.objects.create_user(email="someone@example.com", username="admin")

    with pytest.raises(CommandError, match="belongs to another account"):
        call_command("ensure_admin")

    assert not User.objects.filter(email=ADMIN).exists()
