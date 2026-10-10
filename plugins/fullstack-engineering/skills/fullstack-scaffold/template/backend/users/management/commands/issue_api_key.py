from django.core.management.base import BaseCommand, CommandError

from backend.users.models import ApiKey, User


class Command(BaseCommand):
    help = "Issue an API key for a user. The key is printed once and never stored."

    def add_arguments(self, parser):
        parser.add_argument("email")
        parser.add_argument("name", help="What the key is for, e.g. 'desktop client'")

    def handle(self, *args, **options):
        try:
            user = User.objects.get(email=options["email"])
        except User.DoesNotExist as exc:
            raise CommandError(f"No user with email {options['email']}") from exc
        _, raw_key = ApiKey.issue(user, options["name"])
        self.stdout.write(raw_key)
