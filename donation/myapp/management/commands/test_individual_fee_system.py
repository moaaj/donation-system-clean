from django.core.management.base import BaseCommand
from myapp.models import Student, FeeCategory, IndividualStudentFee, User, UserProfile
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Test the individual fee system - create a fee and verify it appears for the student'

    def handle(self, *args, **options):
        try:
            # Find tamim123 user and student
            user = User.objects.get(username='tamim123')
            user_profile = user.myapp_profile
            student = user_profile.student
            
            if not student:
                self.stdout.write(
                    self.style.ERROR('✗ No student profile found for tamim123')
                )
                return
            
            self.stdout.write(f'✓ Found student: {student.first_name} {student.last_name} ({student.student_id})')
            
            # Get demerit penalties category
            category = FeeCategory.objects.get(name='Demerit Penalties', category_type='individual')
            self.stdout.write(f'✓ Found category: {category.name}')
            
            # Check existing individual fees for this student
            existing_fees = IndividualStudentFee.objects.filter(student=student)
            self.stdout.write(f'✓ Current individual fees for {student.first_name}: {existing_fees.count()}')
            
            for fee in existing_fees:
                status = "PAID" if fee.is_paid else "UNPAID"
                self.stdout.write(f'  - {fee.name}: RM {fee.amount} ({status})')
            
            # Create a new test fee
            fee = IndividualStudentFee.objects.create(
                student=student,
                category=category,
                name='Test Penalty from Admin',
                description='This is a test penalty created by admin to verify the system works',
                amount=100.00,
                due_date=timezone.now().date() + timedelta(days=14),
                is_paid=False,
                is_active=True,
                created_by=user
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created test fee: {fee.name} - RM {fee.amount}')
            )
            
            # Verify the fee appears in the student's unpaid fees
            unpaid_fees = IndividualStudentFee.objects.filter(
                student=student,
                is_active=True,
                is_paid=False
            )
            
            self.stdout.write(f'✓ Unpaid fees for {student.first_name}: {unpaid_fees.count()}')
            for fee in unpaid_fees:
                self.stdout.write(f'  - {fee.name}: RM {fee.amount} (Due: {fee.due_date})')
            
            # Test the query that the student view uses
            student_view_fees = IndividualStudentFee.objects.filter(
                student=student, 
                is_active=True,
                is_paid=False
            ).select_related('category').order_by('-created_at')
            
            self.stdout.write(f'✓ Student view would show: {student_view_fees.count()} fees')
            
            if student_view_fees.count() > 0:
                self.stdout.write(
                    self.style.SUCCESS('✓ SUCCESS: Individual fee system is working correctly!')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('✗ ERROR: No fees found in student view query')
                )
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('✗ User tamim123 not found')
            )
        except UserProfile.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('✗ User profile not found for tamim123')
            )
        except FeeCategory.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('✗ Demerit Penalties category not found')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error: {e}')
            )
