from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Create a waqaf admin user'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Username for the waqaf admin')
        parser.add_argument('--email', type=str, help='Email for the waqaf admin')
        parser.add_argument('--password', type=str, help='Password for the waqaf admin')
        parser.add_argument('--first-name', type=str, help='First name for the waqaf admin')
        parser.add_argument('--last-name', type=str, help='Last name for the waqaf admin')

    def handle(self, *args, **options):
        username = options.get('username') or 'waqaf_admin'
        email = options.get('email') or 'waqaf_admin@example.com'
        password = options.get('password') or 'waqaf_admin123'
        first_name = options.get('first_name') or 'Waqaf'
        last_name = options.get('last_name') or 'Admin'

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'User "{username}" already exists.')
            )
            return

        # Create the user
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_staff=True,  # Required for admin access
                is_active=True
            )
            
            # Create or update user profile with waqaf admin role
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'role': 'waqaf_admin'}
            )
            
            if not created:
                profile.role = 'waqaf_admin'
                profile.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created waqaf admin user:\n'
                    f'Username: {username}\n'
                    f'Email: {email}\n'
                    f'Password: {password}\n'
                    f'Role: waqaf_admin\n'
                    f'Access URL: /waqaf-admin/'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating waqaf admin user: {e}')
            )
