import pytest

from backend.users.models import ApiKey, User, hash_api_key


@pytest.mark.django_db
def test_issued_key_is_stored_hashed_and_resolves():
    user = User.objects.create_user(email="a@example.com", password="pw-123456")
    api_key, raw_key = ApiKey.issue(user, "desktop")

    assert api_key.hashed_key == hash_api_key(raw_key)
    assert raw_key not in api_key.hashed_key
    assert ApiKey.resolve(raw_key).user == user


@pytest.mark.django_db
def test_revoked_key_does_not_resolve():
    user = User.objects.create_user(email="b@example.com", password="pw-123456")
    api_key, raw_key = ApiKey.issue(user, "script")
    api_key.revoked_at = api_key.created_at
    api_key.save()

    assert ApiKey.resolve(raw_key) is None
