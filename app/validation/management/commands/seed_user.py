from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a login user, or reset its password if it already exists."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--password", required=True)

    def handle(self, *args, username, password, **options):
        user, created = get_user_model().objects.get_or_create(username=username)
        user.set_password(password)
        user.save()
        self.stdout.write(f"{'Created' if created else 'Updated'} user {username!r}")
