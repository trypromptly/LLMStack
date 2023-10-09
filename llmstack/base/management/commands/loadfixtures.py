import os

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create admin user if no users exist'

    def handle(self, *args, **options):
        if not User.objects.exists():
            User.objects.create_superuser(os.getenv('ADMIN_USERNAME', 'admin'), os.getenv(
                'ADMIN_EMAIL', ''), os.getenv('ADMIN_PASSWORD', 'promptly'))
            self.stdout.write(self.style.SUCCESS('Admin user created.'))

            try:
                call_command('loaddata', 'llmstack/fixtures/initial_data.json')
                self.stdout.write(self.style.SUCCESS('Initial data loaded.'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    'Error loading initial data.'))
                self.stdout.write(self.style.ERROR(e))
