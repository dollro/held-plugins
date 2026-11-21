"""Keep the admin account in line with the env: DJANGO_SUPERUSER_EMAIL (required),
DJANGO_SUPERUSER_USERNAME and DJANGO_SUPERUSER_PASSWORD (both optional).

Runs after migrate on every deploy (scripts/deploy.sh) and on every start of
the local stack; redeploying the same tag applies a changed password. Dev,
staging and production use the same command and keys. Idempotent:

- DJANGO_SUPERUSER_PASSWORD set: the source of truth. A new admin gets it; an
  existing admin whose password differs is updated, so a changed value takes
  effect on the next deploy or start. An unchanged password keeps its hash
  (checked first), so sessions survive. It must pass the password validators.
- Unset: a new admin gets an unusable password and sets one through the password
  reset mail (nothing stored anywhere); an existing admin's password is left alone.
- An existing non-admin with that email is never promoted.

The password is never printed.
"""

import os

from allauth.account.models import EmailAddress
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from backend.users.models import User


class Command(BaseCommand):
    help = (
        "Create or update the admin from DJANGO_SUPERUSER_EMAIL/PASSWORD (idempotent)."
    )

    def handle(self, *args, **options):
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "").strip()
        if not email:
            raise CommandError("DJANGO_SUPERUSER_EMAIL is not set.")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")
        existing = User.objects.filter(email__iexact=email).first()
        if existing is not None:
            self._update(existing, password)
            return
        self._create(email, password)

    def _create(self, email: str, password: str) -> None:
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "").strip() or email
        if User.objects.filter(username=username).exists():
            raise CommandError(
                f"Username {username} belongs to another account; "
                f"set DJANGO_SUPERUSER_USERNAME to a free one for {email}."
            )
        if password:
            self._validate(password, User(username=username, email=email))
        with transaction.atomic():
            user = User.objects.create_superuser(email=email, username=username)
            self._set_password(user, password)
            # Set by an operator, so the address counts as verified. With SSO, use
            # the admin's company address (a domain in SSO_VERIFIED_EMAIL_DOMAINS):
            # the first SSO login then connects to this account.
            EmailAddress.objects.create(
                user=user, email=email, verified=True, primary=True
            )
        how = (
            "with the password from the env"
            if password
            else "without a password (reset mail)"
        )
        self.stdout.write(self.style.SUCCESS(f"Admin {email} created {how}."))

    def _update(self, user: User, password: str) -> None:
        if not user.is_superuser:
            raise CommandError(
                f"{user.email} exists but is not an admin; not promoting it."
            )
        # check_password first: an unchanged password keeps its hash and sessions.
        if not password or user.check_password(password):
            self.stdout.write(f"Admin {user.email} unchanged.")
            return
        self._validate(password, user)
        self._set_password(user, password)
        self.stdout.write(
            self.style.SUCCESS(f"Admin {user.email}: password set from the env.")
        )

    @staticmethod
    def _validate(password: str, user: User) -> None:
        try:
            validate_password(password, user)
        except ValidationError as error:
            raise CommandError(
                "DJANGO_SUPERUSER_PASSWORD is too weak: " + " ".join(error.messages)
            ) from None

    @staticmethod
    def _set_password(user: User, password: str) -> None:
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(update_fields=["password"])
