from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from myapp.models import UserProfile, ModulePermission, SchoolFeesLevelAdmin

class Command(BaseCommand):
    help = 'Sets up module-specific admin users and permissions.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-users',
            action='store_true',
            help='Create example admin users for each module.',
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Username for the admin user to create.',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email for the admin user to create.',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Password for the admin user to create.',
        )
        parser.add_argument(
            '--role',
            type=str,
            choices=['donation_admin', 'waqaf_admin', 'school_fees_admin', 'school_fees_level_admin'],
            help='Role for the admin user to create.',
        )
        parser.add_argument(
            '--level',
            type=str,
            choices=['form1', 'form2', 'form3', 'form4', 'form5', 'year1', 'year2', 'year3', 'year4', 'year5', 'standard1', 'standard2', 'standard3', 'standard4', 'standard5', 'standard6', 'all'],
            help='Level for school fees level admin (only for school_fees_level_admin role).',
        )

    def handle(self, *args, **options):
        if options['create_users']:
            self.create_example_users()
        elif options['username'] and options['email'] and options['password'] and options['role']:
            self.create_admin_user(
                options['username'],
                options['email'],
                options['password'],
                options['role'],
                options.get('level', 'all')
            )
        else:
            self.show_help()

    def create_example_users(self):
        """Create example admin users for each module"""
        example_users = [
            {
                'username': 'donation_admin',
                'email': 'donation@school.edu',
                'password': 'admin123',
                'role': 'donation_admin',
                'first_name': 'Donation',
                'last_name': 'Admin'
            },
            {
                'username': 'waqaf_admin',
                'email': 'waqaf@school.edu',
                'password': 'admin123',
                'role': 'waqaf_admin',
                'first_name': 'Waqaf',
                'last_name': 'Admin'
            },
            {
                'username': 'school_fees_admin',
                'email': 'schoolfees@school.edu',
                'password': 'admin123',
                'role': 'school_fees_admin',
                'first_name': 'School Fees',
                'last_name': 'Admin'
            },
            {
                'username': 'form1_admin',
                'email': 'form1@school.edu',
                'password': 'admin123',
                'role': 'school_fees_level_admin',
                'first_name': 'Form 1',
                'last_name': 'Admin',
                'level': 'form1'
            },
            {
                'username': 'form2_admin',
                'email': 'form2@school.edu',
                'password': 'admin123',
                'role': 'school_fees_level_admin',
                'first_name': 'Form 2',
                'last_name': 'Admin',
                'level': 'form2'
            }
        ]

        for user_data in example_users:
            self.create_admin_user(
                user_data['username'],
                user_data['email'],
                user_data['password'],
                user_data['role'],
                user_data.get('level', 'all'),
                user_data.get('first_name', ''),
                user_data.get('last_name', '')
            )

    def create_admin_user(self, username, email, password, role, level='all', first_name='', last_name=''):
        """Create an admin user with the specified role and permissions"""
        # Create or get user
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'is_staff': True,
                'is_active': True
            }
        )
        
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Created user: {username}'))
        else:
            self.stdout.write(self.style.WARNING(f'User {username} already exists'))

        # Create or update user profile
        profile, profile_created = UserProfile.objects.get_or_create(
            user=user,
            defaults={'role': role}
        )
        
        if not profile_created:
            profile.role = role
            profile.save()
            self.stdout.write(self.style.SUCCESS(f'Updated profile for: {username}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Created profile for: {username}'))

        # Set up module permissions based on role
        if role == 'donation_admin':
            self.setup_donation_permissions(profile)
        elif role == 'waqaf_admin':
            self.setup_waqaf_permissions(profile)
        elif role == 'school_fees_admin':
            self.setup_school_fees_permissions(profile)
        elif role == 'school_fees_level_admin':
            self.setup_school_fees_level_permissions(profile, level)

    def setup_donation_permissions(self, profile):
        """Set up donation module permissions"""
        ModulePermission.objects.get_or_create(
            user_profile=profile,
            module='donation',
            defaults={
                'can_view': True,
                'can_add': True,
                'can_change': True,
                'can_delete': True,
                'can_manage_settings': True
            }
        )
        ModulePermission.objects.get_or_create(
            user_profile=profile,
            module='pibg_donation',
            defaults={
                'can_view': True,
                'can_add': True,
                'can_change': True,
                'can_delete': True,
                'can_manage_settings': True
            }
        )
        self.stdout.write(self.style.SUCCESS('Set up donation module permissions'))

    def setup_waqaf_permissions(self, profile):
        """Set up waqaf module permissions"""
        ModulePermission.objects.get_or_create(
            user_profile=profile,
            module='waqaf',
            defaults={
                'can_view': True,
                'can_add': True,
                'can_change': True,
                'can_delete': True,
                'can_manage_settings': True
            }
        )
        self.stdout.write(self.style.SUCCESS('Set up waqaf module permissions'))

    def setup_school_fees_permissions(self, profile):
        """Set up school fees module permissions"""
        ModulePermission.objects.get_or_create(
            user_profile=profile,
            module='school_fees',
            defaults={
                'can_view': True,
                'can_add': True,
                'can_change': True,
                'can_delete': True,
                'can_manage_settings': True
            }
        )
        self.stdout.write(self.style.SUCCESS('Set up school fees module permissions'))

    def setup_school_fees_level_permissions(self, profile, level):
        """Set up school fees level-specific permissions"""
        SchoolFeesLevelAdmin.objects.get_or_create(
            user_profile=profile,
            level=level,
            defaults={
                'can_view': True,
                'can_add': True,
                'can_change': True,
                'can_delete': True,
                'can_manage_fees': True,
                'can_manage_payments': True
            }
        )
        self.stdout.write(self.style.SUCCESS(f'Set up school fees level permissions for: {level}'))

    def show_help(self):
        """Show help information"""
        self.stdout.write(self.style.HTTP_INFO('\nModule Admin Setup Commands:'))
        self.stdout.write('\n1. Create example admin users:')
        self.stdout.write('   python manage.py setup_module_admins --create-users')
        self.stdout.write('\n2. Create specific admin user:')
        self.stdout.write('   python manage.py setup_module_admins --username john --email john@school.edu --password admin123 --role donation_admin')
        self.stdout.write('\n3. Create school fees level admin:')
        self.stdout.write('   python manage.py setup_module_admins --username form1_admin --email form1@school.edu --password admin123 --role school_fees_level_admin --level form1')
        self.stdout.write('\nAvailable roles:')
        self.stdout.write('   - donation_admin: Donation Module Admin')
        self.stdout.write('   - waqaf_admin: Waqaf Module Admin')
        self.stdout.write('   - school_fees_admin: School Fees Module Admin')
        self.stdout.write('   - school_fees_level_admin: School Fees Level Admin')
        self.stdout.write('\nAvailable levels for school fees level admin:')
        self.stdout.write('   - form1, form2, form3, form4, form5')
        self.stdout.write('   - year1, year2, year3, year4, year5')
        self.stdout.write('   - standard1, standard2, standard3, standard4, standard5, standard6')
        self.stdout.write('   - all: All levels')
