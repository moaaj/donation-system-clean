from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from myapp.models import UserProfile, SchoolFeesLevelAdmin

class Command(BaseCommand):
    help = 'Set up form1_admin user with Form 1 level permissions'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='form1_admin', help='Username for the Form 1 admin')
        parser.add_argument('--email', type=str, default='form1_admin@school.edu', help='Email for the Form 1 admin')
        parser.add_argument('--password', type=str, default='form1admin123', help='Password for the Form 1 admin')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        
        # Create or get the user
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': 'Form 1',
                'last_name': 'Admin',
                'is_staff': True,
                'is_active': True,
            }
        )
        
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Created user: {username}'))
        else:
            self.stdout.write(self.style.WARNING(f'User already exists: {username}'))
        
        # Create or update user profile
        profile, profile_created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'role': 'school_fees_level_admin',
                'phone_number': '0123456789',
            }
        )
        
        if not profile_created:
            # Update existing profile
            profile.role = 'school_fees_level_admin'
            profile.save()
            self.stdout.write(self.style.WARNING(f'Updated profile for: {username}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Created profile for: {username}'))
        
        # Create or update level assignment for Form 1
        level_assignment, assignment_created = SchoolFeesLevelAdmin.objects.get_or_create(
            user_profile=profile,
            level='form1',
            defaults={
                'can_view': True,
                'can_add': True,
                'can_change': True,
                'can_delete': False,
                'can_manage_fees': True,
                'can_manage_payments': True,
            }
        )
        
        if not assignment_created:
            # Update existing assignment
            level_assignment.can_view = True
            level_assignment.can_add = True
            level_assignment.can_change = True
            level_assignment.can_delete = False
            level_assignment.can_manage_fees = True
            level_assignment.can_manage_payments = True
            level_assignment.save()
            self.stdout.write(self.style.WARNING(f'Updated level assignment for: {username}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Created level assignment for: {username}'))
        
        # Test the setup
        if profile.is_form1_admin():
            self.stdout.write(self.style.SUCCESS(f'✅ {username} is correctly set up as Form 1 admin'))
            self.stdout.write(f'   - Role: {profile.role}')
            self.stdout.write(f'   - Assigned levels: {profile.get_assigned_levels()}')
            self.stdout.write(f'   - Can view: {level_assignment.can_view}')
            self.stdout.write(f'   - Can manage fees: {level_assignment.can_manage_fees}')
            self.stdout.write(f'   - Can manage payments: {level_assignment.can_manage_payments}')
        else:
            self.stdout.write(self.style.ERROR(f'❌ {username} is NOT correctly set up as Form 1 admin'))
        
        self.stdout.write(self.style.SUCCESS(f'\nForm 1 admin setup complete!'))
        self.stdout.write(f'Username: {username}')
        self.stdout.write(f'Password: {password}')
        self.stdout.write(f'Dashboard URL: /form1-admin/')
        self.stdout.write(f'Students URL: /form1-admin/students/')
