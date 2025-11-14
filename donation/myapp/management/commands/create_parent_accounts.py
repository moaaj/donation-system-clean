from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
import random
import string

from myapp.models import Student, Parent


class Command(BaseCommand):
    help = 'Create parent accounts for all students'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing parent accounts before creating new ones',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing parent accounts...')
            Parent.objects.all().delete()
            User.objects.filter(username__startswith='parent_').delete()
            self.stdout.write('Existing parent accounts cleared.')

        self.stdout.write('Creating parent accounts for all students...')
        
        with transaction.atomic():
            self.create_parent_accounts()

        self.stdout.write(
            self.style.SUCCESS('Successfully created parent accounts!')
        )

    def generate_nric(self):
        """Generate a random NRIC for parent"""
        return f"{random.randint(100000, 999999):06d}{random.randint(10, 99):02d}{random.randint(1000, 9999):04d}"

    def generate_phone(self):
        """Generate a random phone number"""
        return f"01{random.randint(1, 9)}{random.randint(1000000, 9999999):07d}"

    def generate_address(self):
        """Generate a random address"""
        addresses = [
            "No. 123, Jalan Merdeka, Taman Harmoni, 50000 Kuala Lumpur",
            "45, Lorong Bayu 3/2, Bandar Sunway, 47500 Selangor",
            "78, Jalan Perdana 5, Taman Megah, 40000 Shah Alam",
            "12, Jalan Seri Kembangan, Bandar Baru Bangi, 43000 Selangor",
            "56, Persiaran Raja Muda, Mont Kiara, 50480 Kuala Lumpur",
            "89, Jalan SS2/24, Petaling Jaya, 47300 Selangor",
            "34, Jalan Ampang Hilir, Ampang, 55000 Kuala Lumpur",
            "67, Jalan Bukit Bintang, Bukit Bintang, 55100 Kuala Lumpur",
        ]
        return random.choice(addresses)

    def create_parent_accounts(self):
        """Create parent accounts for all students"""
        students = Student.objects.filter(is_active=True)
        
        # Group students by similar last names (family groups)
        family_groups = {}
        for student in students:
            family_key = student.last_name.lower()
            if family_key not in family_groups:
                family_groups[family_key] = []
            family_groups[family_key].append(student)

        parent_count = 0
        
        for family_name, family_students in family_groups.items():
            # Create one or two parents per family
            num_parents = random.choice([1, 2])  # Single parent or both parents
            
            for parent_num in range(num_parents):
                # Generate parent details
                if parent_num == 0:  # First parent (usually father)
                    parent_names = {
                        'abdullah': ['Ahmad Abdullah', 'Mohammad Abdullah'],
                        'rahman': ['Abdul Rahman', 'Mohd Rahman'],
                        'hassan': ['Ibrahim Hassan', 'Yusuf Hassan'],
                        'ahmad': ['Ali Ahmad', 'Omar Ahmad'],
                        'smith': ['John Smith', 'David Smith'],
                        'johnson': ['Michael Johnson', 'Robert Johnson'],
                        'brown': ['James Brown', 'William Brown'],
                        'tan': ['Tan Wei Ming', 'Tan Chee Keong'],
                        'lee': ['Lee Seng Huat', 'Lee Kim Seng'],
                        'lim': ['Lim Boon Keat', 'Lim Chong Wei'],
                        'wong': ['Wong Ah Kow', 'Wong Yee Sang'],
                    }
                else:  # Second parent (usually mother)
                    parent_names = {
                        'abdullah': ['Siti Abdullah', 'Fatimah Abdullah'],
                        'rahman': ['Khadijah Rahman', 'Aminah Rahman'],
                        'hassan': ['Zainab Hassan', 'Maryam Hassan'],
                        'ahmad': ['Aisha Ahmad', 'Noor Ahmad'],
                        'smith': ['Mary Smith', 'Sarah Smith'],
                        'johnson': ['Jennifer Johnson', 'Lisa Johnson'],
                        'brown': ['Susan Brown', 'Patricia Brown'],
                        'tan': ['Tan Mei Ling', 'Tan Siew Hoon'],
                        'lee': ['Lee Hui Min', 'Lee Pei Shan'],
                        'lim': ['Lim Ai Ling', 'Lim Soo Cheng'],
                        'wong': ['Wong Lai Fong', 'Wong Mun Yee'],
                    }

                # Get appropriate name for this family
                possible_names = parent_names.get(family_name, ['Parent ' + family_name.title()])
                full_name = random.choice(possible_names)
                
                # Split name
                name_parts = full_name.split(' ', 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else family_name.title()

                # Create username
                username = f"parent_{family_name}_{parent_num + 1}_{random.randint(100, 999)}"
                
                # Create user account
                user = User.objects.create_user(
                    username=username,
                    email=f"{username}@example.com",
                    password='parent123',  # Default password
                    first_name=first_name,
                    last_name=last_name
                )

                # Create parent profile
                parent = Parent.objects.create(
                    user=user,
                    nric=self.generate_nric(),
                    phone_number=self.generate_phone(),
                    address=self.generate_address()
                )

                # Link all children in this family to this parent
                for student in family_students:
                    parent.students.add(student)

                parent_count += 1
                
                self.stdout.write(
                    f'Created parent: {full_name} (username: {username}) for {len(family_students)} children'
                )

        self.stdout.write(f'Total parents created: {parent_count}')
        self.stdout.write(f'Total families: {len(family_groups)}')
        
        # Show some login credentials
        self.stdout.write(self.style.SUCCESS(
            f'\n=== SAMPLE LOGIN CREDENTIALS ===\n'
            f'All parents have the default password: parent123\n'
            f'Sample usernames: {User.objects.filter(username__startswith="parent_")[:5].values_list("username", flat=True)}\n'
            f'Parents can login at /accounts/login/ and access their portal\n'
        ))
