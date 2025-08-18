from django.core.management.base import BaseCommand
from myapp.models import FeeStructure, FeeCategory, Student, FeeStatus
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Test the monthly payment feature by creating a sample monthly fee structure'

    def handle(self, *args, **options):
        try:
            # Get or create a test category
            category, created = FeeCategory.objects.get_or_create(
                name='Test Monthly Category',
                defaults={
                    'description': 'Test category for monthly payments',
                    'category_type': 'general',
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(f'✓ Created test category: {category.name}')
            else:
                self.stdout.write(f'✓ Using existing category: {category.name}')
            
            # Create a test monthly fee structure
            fee_structure = FeeStructure.objects.create(
                category=category,
                form='Test Form',
                amount=100.00,  # This will be calculated automatically
                frequency='monthly',
                monthly_duration=10,
                total_amount=1000.00,
                auto_generate_payments=True,
                is_active=True
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created monthly fee structure: {fee_structure}')
            )
            self.stdout.write(f'  - Total Amount: RM {fee_structure.total_amount}')
            self.stdout.write(f'  - Monthly Amount: RM {fee_structure.get_monthly_amount()}')
            self.stdout.write(f'  - Duration: {fee_structure.monthly_duration} months')
            
            # Test auto-generation for all students
            active_students = Student.objects.filter(is_active=True)
            self.stdout.write(f'✓ Found {active_students.count()} active students')
            
            total_generated = 0
            for student in active_students:
                payments = fee_structure.generate_monthly_payments_for_student(student)
                total_generated += len(payments)
                self.stdout.write(f'  - Generated {len(payments)} payments for {student.first_name} {student.last_name}')
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Successfully generated {total_generated} monthly payment records!')
            )
            
            # Show some sample payment records
            sample_payments = FeeStatus.objects.filter(fee_structure=fee_structure)[:5]
            self.stdout.write('\nSample payment records:')
            for payment in sample_payments:
                self.stdout.write(f'  - {payment.student.first_name}: RM {payment.amount} (Due: {payment.due_date})')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error: {e}')
            )
