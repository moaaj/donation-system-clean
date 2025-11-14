from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
import random
from decimal import Decimal

from myapp.models import (
    Student, FeeCategory, FeeStructure, Payment, FeeStatus
)


class Command(BaseCommand):
    help = 'Populate the database with dummy data for school fees system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before populating',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            self.clear_data()

        self.stdout.write('Starting to populate dummy data...')
        
        with transaction.atomic():
            # 1. Create Fee Categories
            self.create_fee_categories()
            
            # 2. Create Students
            self.create_students()
            
            # 3. Create Fee Structures
            self.create_fee_structures()
            
            # 4. Create Payments and Fee Statuses
            self.create_payments_and_statuses()

        self.stdout.write(
            self.style.SUCCESS('Successfully populated dummy data!')
        )

    def clear_data(self):
        """Clear existing data"""
        FeeStatus.objects.all().delete()
        Payment.objects.all().delete()
        FeeStructure.objects.all().delete()
        Student.objects.all().delete()
        FeeCategory.objects.all().delete()
        self.stdout.write('Existing data cleared.')

    def create_fee_categories(self):
        """Create fee categories: PTA, Activities, Exams, Dormitory"""
        categories_data = [
            {
                'name': 'PTA',
                'description': 'Parent Teacher Association fees for school activities and events',
                'category_type': 'general'
            },
            {
                'name': 'Activities',
                'description': 'Extracurricular activities and sports fees',
                'category_type': 'general'
            },
            {
                'name': 'Exams',
                'description': 'Examination and assessment fees',
                'category_type': 'general'
            },
            {
                'name': 'Dormitory',
                'description': 'Hostel and accommodation fees for boarding students',
                'category_type': 'general'
            },
        ]

        for cat_data in categories_data:
            category, created = FeeCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')

    def create_students(self):
        """Create students for Forms 1-5, Classes A-B"""
        forms = ['1', '2', '3', '4', '5']
        classes = ['A', 'B']
        
        student_count = 0
        for form in forms:
            for class_name in classes:
                # Create different number of students per class (realistic distribution)
                if form == '1':
                    male_count = random.randint(18, 22)
                    female_count = random.randint(16, 20)
                elif form == '2':
                    male_count = random.randint(18, 22)
                    female_count = random.randint(19, 25)
                elif form == '3':
                    male_count = random.randint(20, 26)
                    female_count = random.randint(21, 25)
                elif form == '4':
                    male_count = random.randint(22, 28)
                    female_count = random.randint(24, 28)
                else:  # Form 5
                    male_count = random.randint(24, 30)
                    female_count = random.randint(26, 30)

                # Create male students
                for i in range(male_count):
                    student_count += 1
                    student_id = f"STD{student_count:04d}"
                    nric = f"{random.randint(100000, 999999):06d}{random.randint(10, 99):02d}{random.randint(1000, 9999):04d}"
                    
                    first_names_male = [
                        'Ahmad', 'Ali', 'Hassan', 'Ibrahim', 'Ismail', 'Muhammad', 'Omar', 'Yusuf',
                        'Adam', 'Daniel', 'David', 'James', 'John', 'Michael', 'Peter', 'Robert',
                        'Chen', 'Lee', 'Lim', 'Tan', 'Wong', 'Ng', 'Ong', 'Teo'
                    ]
                    last_names = [
                        'Abdullah', 'Rahman', 'Hassan', 'Ahmad', 'Ali', 'Ibrahim',
                        'Smith', 'Johnson', 'Brown', 'Davis', 'Miller', 'Wilson',
                        'Tan', 'Lee', 'Lim', 'Wong', 'Ng', 'Ong', 'Teo', 'Goh'
                    ]
                    
                    student = Student.objects.create(
                        student_id=student_id,
                        nric=nric,
                        first_name=random.choice(first_names_male),
                        last_name=random.choice(last_names),
                        class_name=class_name,
                        program=f'Science Stream' if random.choice([True, False]) else 'Arts Stream',
                        level='form',
                        level_custom=form,
                        year_batch=2024,
                        is_active=True
                    )

                # Create female students
                for i in range(female_count):
                    student_count += 1
                    student_id = f"STD{student_count:04d}"
                    nric = f"{random.randint(100000, 999999):06d}{random.randint(10, 99):02d}{random.randint(1000, 9999):04d}"
                    
                    first_names_female = [
                        'Aisha', 'Fatima', 'Khadijah', 'Maryam', 'Noor', 'Siti', 'Zainab', 'Aminah',
                        'Emily', 'Emma', 'Jessica', 'Lisa', 'Maria', 'Sarah', 'Sophie', 'Victoria',
                        'Mei', 'Hui', 'Lin', 'Ying', 'Wei', 'Xin', 'Li', 'Yan'
                    ]
                    
                    student = Student.objects.create(
                        student_id=student_id,
                        nric=nric,
                        first_name=random.choice(first_names_female),
                        last_name=random.choice(last_names),
                        class_name=class_name,
                        program=f'Science Stream' if random.choice([True, False]) else 'Arts Stream',
                        level='form',
                        level_custom=form,
                        year_batch=2024,
                        is_active=True
                    )

                self.stdout.write(f'Created {male_count + female_count} students for Form {form} Class {class_name}')

        self.stdout.write(f'Total students created: {student_count}')

    def create_fee_structures(self):
        """Create fee structures for each category and form"""
        categories = FeeCategory.objects.all()
        forms = ['1', '2', '3', '4', '5']
        
        # Fee amounts per category per form (in RM)
        fee_amounts = {
            'PTA': {
                '1': Decimal('200.00'),
                '2': Decimal('220.00'),
                '3': Decimal('240.00'),
                '4': Decimal('260.00'),
                '5': Decimal('280.00'),
            },
            'Activities': {
                '1': Decimal('150.00'),
                '2': Decimal('160.00'),
                '3': Decimal('170.00'),
                '4': Decimal('180.00'),
                '5': Decimal('200.00'),
            },
            'Exams': {
                '1': Decimal('180.00'),
                '2': Decimal('190.00'),
                '3': Decimal('200.00'),
                '4': Decimal('220.00'),
                '5': Decimal('250.00'),
            },
            'Dormitory': {
                '1': Decimal('300.00'),
                '2': Decimal('320.00'),
                '3': Decimal('340.00'),
                '4': Decimal('360.00'),
                '5': Decimal('400.00'),
            },
        }

        for category in categories:
            for form in forms:
                amount = fee_amounts.get(category.name, {}).get(form, Decimal('200.00'))
                
                fee_structure, created = FeeStructure.objects.get_or_create(
                    category=category,
                    form=form,
                    defaults={
                        'amount': amount,
                        'frequency': 'yearly',
                        'is_active': True
                    }
                )
                
                if created:
                    self.stdout.write(f'Created fee structure: {category.name} - Form {form} - RM {amount}')

    def create_payments_and_statuses(self):
        """Create payment records and fee statuses with realistic distribution"""
        students = Student.objects.all()
        fee_structures = FeeStructure.objects.all()
        
        payment_count = 0
        fee_status_count = 0
        
        # Create payment records for each student
        for student in students:
            # Get fee structures for this student's form
            student_form = student.level_custom
            student_fee_structures = fee_structures.filter(form=student_form)
            
            for fee_structure in student_fee_structures:
                # Determine payment status based on realistic distribution
                # 85% paid, 10% pending, 5% overdue
                status_choice = random.choices(
                    ['completed', 'pending', 'overdue'],
                    weights=[85, 10, 5],
                    k=1
                )[0]
                
                # Create payment record if completed
                if status_choice == 'completed':
                    # Random payment date in the last 6 months
                    payment_date = timezone.now().date() - timedelta(
                        days=random.randint(1, 180)
                    )
                    
                    payment = Payment.objects.create(
                        student=student,
                        fee_structure=fee_structure,
                        amount=fee_structure.amount,
                        payment_date=payment_date,
                        payment_method=random.choice(['cash', 'bank_transfer', 'online']),
                        status='completed',
                        receipt_number=f'RCP{payment_count + 1:06d}'
                    )
                    payment_count += 1
                
                # Create fee status record
                if status_choice in ['pending', 'overdue']:
                    due_date = timezone.now().date() + timedelta(
                        days=random.randint(-30, 30)  # Some overdue, some future
                    )
                    
                    # Adjust status based on due date
                    if due_date < timezone.now().date():
                        actual_status = 'overdue'
                    else:
                        actual_status = 'pending'
                    
                    fee_status = FeeStatus.objects.create(
                        student=student,
                        fee_structure=fee_structure,
                        amount=fee_structure.amount,
                        due_date=due_date,
                        status=actual_status
                    )
                    fee_status_count += 1

        self.stdout.write(f'Created {payment_count} payment records')
        self.stdout.write(f'Created {fee_status_count} fee status records')

        # Summary statistics
        total_students = students.count()
        total_completed = Payment.objects.filter(status='completed').count()
        total_pending = FeeStatus.objects.filter(status='pending').count()
        total_overdue = FeeStatus.objects.filter(status='overdue').count()
        
        self.stdout.write(self.style.SUCCESS(
            f'\n=== SUMMARY ===\n'
            f'Total Students: {total_students}\n'
            f'Completed Payments: {total_completed}\n'
            f'Pending Payments: {total_pending}\n'
            f'Overdue Payments: {total_overdue}\n'
        ))
