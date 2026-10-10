import os

from allauth.account.models import EmailAddress
from django.core.management.base import BaseCommand, CommandError

from backend.users.models import User


class Command(BaseCommand):
    help = "Create the end-to-end test user (local and CI only)."

    def handle(self, *args, **options):
        if "production" in os.environ.get("DJANGO_SETTINGS_MODULE", ""):
            raise CommandError("Refusing to seed a test user with production settings.")
        email = os.environ.get("E2E_USER_EMAIL", "e2e@example.com")
        password = os.environ.get("E2E_USER_PASSWORD", "e2e-password-123")
        user, created = User.objects.get_or_create(
            email=email, defaults={"username": email}
        )
        user.set_password(password)
        user.save()
        EmailAddress.objects.update_or_create(
            user=user, email=email, defaults={"verified": True, "primary": True}
        )
        self.stdout.write(f"E2E user {email} {'created' if created else 'updated'}.")
