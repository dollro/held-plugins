import os

from allauth.account.models import EmailAddress
from django.core.management.base import BaseCommand

from backend.users.models import User


class Command(BaseCommand):
    help = "Create the superuser from DJANGO_SUPERUSER_EMAIL/PASSWORD if it does not exist."

    def handle(self, *args, **options):
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        if not email or not password:
            self.stdout.write("DJANGO_SUPERUSER_EMAIL/PASSWORD not set; skipping.")
            return
        if User.objects.filter(email=email).exists():
            self.stdout.write(f"Superuser {email} exists.")
            return
        user = User.objects.create_superuser(email=email, password=password)
        # Set by an operator, so the address counts as verified. With SSO, use the
        # admin's company address (a domain in SSO_VERIFIED_EMAIL_DOMAINS): the
        # first SSO login then connects to this account.
        EmailAddress.objects.create(user=user, email=email, verified=True, primary=True)
        self.stdout.write(f"Superuser {email} created.")
