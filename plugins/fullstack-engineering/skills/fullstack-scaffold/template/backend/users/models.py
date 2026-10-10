import hashlib
import secrets

from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils import timezone


class EmailUserManager(UserManager):
    """Email is the login identifier; username stays as an optional display name."""

    def _create_user(self, username, email, password, **extra_fields):
        email = self.normalize_email(email)
        user = self.model(username=username or email, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(None, email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self._create_user(None, email, password, **extra_fields)


class User(AbstractUser):
    """Custom user from day one: swapping the user model later is a migration project."""

    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = EmailUserManager()

    def __str__(self) -> str:
        return self.email


def hash_api_key(raw_key: str) -> str:
    # API keys are long random strings, so a fast hash is sufficient; never store raw keys.
    return hashlib.sha256(raw_key.encode()).hexdigest()


class ApiKey(models.Model):
    """Credential for non-browser clients (desktop apps, scripts, other services)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="api_keys"
    )
    name = models.CharField(max_length=100)
    prefix = models.CharField(max_length=40, editable=False)
    hashed_key = models.CharField(max_length=64, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.prefix}…)"

    @classmethod
    def issue(cls, user, name: str) -> tuple["ApiKey", str]:
        """Create a key. The raw key is returned once and never stored."""
        raw_key = f"{settings.API_KEY_PREFIX}_{secrets.token_urlsafe(32)}"
        api_key = cls.objects.create(
            user=user,
            name=name,
            prefix=raw_key[: len(settings.API_KEY_PREFIX) + 7],
            hashed_key=hash_api_key(raw_key),
        )
        return api_key, raw_key

    @classmethod
    def resolve(cls, raw_key: str) -> "ApiKey | None":
        api_key = (
            cls.objects.select_related("user")
            .filter(hashed_key=hash_api_key(raw_key), revoked_at__isnull=True)
            .first()
        )
        if api_key is None or not api_key.user.is_active:
            return None
        cls.objects.filter(pk=api_key.pk).update(last_used_at=timezone.now())
        return api_key
