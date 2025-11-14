from django.core.management.base import BaseCommand
from myapp.models import Student, Payment, PibgDonation
from django.db.models import Sum, Count
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Debug Form 3 dashboard data'

    def handle(self, *args, **options):
        self.stdout.write("=== DEBUGGING FORM 3 DASHBOARD ===\n")
        
        # Simulate the exact logic from the view
        form_level = 'form3'
        form_level_value = form_level.replace('form', '')  # '3'
        form_level_text = form_level.replace('form', 'Form ')  # 'Form 3'
        
        self.stdout.write(f"Form level: {form_level}")
        self.stdout.write(f"Form level value: '{form_level_value}'")
        self.stdout.write(f"Form level text: '{form_level_text}'")
        
        # Test the exact filter from the view
        form_students = Student.objects.filter(
            level_custom__in=[form_level_value, form_level_text],
            is_active=True
        )
        
        self.stdout.write(f"\nFiltered students count: {form_students.count()}")
        
        # Show first 10 students
        self.stdout.write(f"\nFirst 10 students:")
        for i, student in enumerate(form_students[:10], 1):
            self.stdout.write(f"{i}. {student.student_id}: {student.first_name} {student.last_name} (level: {student.level_custom}, active: {student.is_active})")
        
        # Test payment calculations
        total_payments = Payment.objects.filter(student__in=form_students).count()
        total_paid = Payment.objects.filter(student__in=form_students, status='completed').count()
        total_revenue = Payment.objects.filter(student__in=form_students, status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
        
        self.stdout.write(f"\nPayment Statistics:")
        self.stdout.write(f"- Total payments: {total_payments}")
        self.stdout.write(f"- Completed payments: {total_paid}")
        self.stdout.write(f"- Total revenue: RM {total_revenue:.2f}")
        
        # Test PIBG donations
        total_pibg_donations = PibgDonation.objects.filter(student__in=form_students, status='completed').count()
        total_pibg_amount = PibgDonation.objects.filter(student__in=form_students, status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
        
        self.stdout.write(f"\nPIBG Donations:")
        self.stdout.write(f"- Total donations: {total_pibg_donations}")
        self.stdout.write(f"- Total amount: RM {total_pibg_amount:.2f}")
        
        # Test class distribution
        class_data = {}
        for student in form_students:
            class_name = student.class_name or 'No Class'
            if class_name not in class_data:
                class_data[class_name] = 0
            class_data[class_name] += 1
        
        self.stdout.write(f"\nClass Distribution:")
        for class_name, count in sorted(class_data.items()):
            self.stdout.write(f"- {class_name}: {count} students")
        
        # Test recent payments
        recent_payments = Payment.objects.filter(student__in=form_students).order_by('-created_at')[:5]
        self.stdout.write(f"\nRecent Payments (last 5):")
        for payment in recent_payments:
            self.stdout.write(f"- {payment.student.first_name} {payment.student.last_name}: RM{payment.amount:.2f}")
        
        # Test recent donations
        recent_donations = PibgDonation.objects.filter(student__in=form_students).order_by('-created_at')[:5]
        self.stdout.write(f"\nRecent Donations (last 5):")
        for donation in recent_donations:
            self.stdout.write(f"- {donation.student.first_name} {donation.student.last_name}: RM{donation.amount:.2f}")
        
        self.stdout.write(f"\n=== DEBUG COMPLETE ===")
        self.stdout.write(f"Expected: 91 students, 309 payments, RM 83,415 revenue")
        self.stdout.write(f"Actual: {form_students.count()} students, {total_payments} payments, RM {total_revenue:.2f} revenue")
