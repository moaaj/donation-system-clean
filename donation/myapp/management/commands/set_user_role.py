from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Set the role for a user in myapp_profile'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str)
        parser.add_argument('role', type=str, choices=['admin', 'student'])

    def handle(self, *args, **options):
        username = options['username']
        role = options['role']
        try:
            user = User.objects.get(username=username)
            profile = user.myapp_profile
            profile.role = role
            profile.save()
            self.stdout.write(self.style.SUCCESS(f"Role for {username} set to {role}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(str(e)))
