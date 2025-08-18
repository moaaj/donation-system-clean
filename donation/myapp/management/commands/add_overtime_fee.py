from django.core.management.base import BaseCommand
from myapp.models import Student, FeeCategory, IndividualStudentFee, User, UserProfile
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Add an overtime individual fee for tamim123 student'

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
            
            # Get overtime category
            category = FeeCategory.objects.get(name='Overtime', category_type='individual')
            
            # Create an overtime fee
            fee = IndividualStudentFee.objects.create(
                student=student,
                category=category,
                name='Late Pickup Fee',
                description='Student was picked up 30 minutes after school hours ended',
                amount=25.00,
                due_date=timezone.now().date() + timedelta(days=3),
                is_paid=False,
                is_active=True,
                created_by=user
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created overtime fee for {student.first_name} {student.last_name}: {fee.name} - RM {fee.amount}')
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
                self.style.ERROR('✗ Overtime category not found')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error: {str(e)}')
            ) 