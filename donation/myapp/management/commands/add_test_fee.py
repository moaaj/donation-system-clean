from django.core.management.base import BaseCommand
from myapp.models import Student, FeeCategory, IndividualStudentFee, User, UserProfile
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Add a test individual fee for tamim123 student'

    def handle(self, *args, **options):
        try:
            # Find tamim123 user and student through UserProfile
            user = User.objects.get(username='tamim123')
            user_profile = user.myapp_profile
            student = user_profile.student
            
            if not student:
                self.stdout.write(
                    self.style.ERROR('✗ No student profile found for tamim123')
                )
                return
            
            # Get demerit penalties category
            category = FeeCategory.objects.get(name='Demerit Penalties', category_type='individual')
            
            # Create a test fee
            fee = IndividualStudentFee.objects.create(
                student=student,
                category=category,
                name='Late to Class Penalty',
                description='Student was late to class on multiple occasions during the week',
                amount=50.00,
                due_date=timezone.now().date() + timedelta(days=7),
                is_paid=False,
                is_active=True,
                created_by=user
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created test fee for {student.first_name} {student.last_name}: {fee.name} - RM {fee.amount}')
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
                self.style.ERROR(f'✗ Error: {str(e)}')
            ) 