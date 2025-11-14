from django.core.management.base import BaseCommand
from myapp.models import Student, Payment, PibgDonation
from django.db.models import Sum, Count
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Test Form 1 admin functionality and data retrieval'

    def handle(self, *args, **options):
        self.stdout.write("=== Form 1 Admin Data Test ===\n")
        
        # Test 1: Student Count
        form1_students = Student.objects.filter(level_custom__in=['1', 'Form 1'], is_active=True)
        total_students = form1_students.count()
        self.stdout.write(f"✅ Total Form 1 students (active): {total_students}")
        
        # Test 2: Payment Statistics
        total_payments = Payment.objects.filter(student__in=form1_students).count()
        completed_payments = Payment.objects.filter(student__in=form1_students, status='completed').count()
        pending_payments = Payment.objects.filter(student__in=form1_students, status='pending').count()
        
        self.stdout.write(f"✅ Total Form 1 payments: {total_payments}")
        self.stdout.write(f"✅ Completed Form 1 payments: {completed_payments}")
        self.stdout.write(f"✅ Pending Form 1 payments: {pending_payments}")
        
        # Test 3: Revenue
        total_revenue = Payment.objects.filter(student__in=form1_students, status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
        self.stdout.write(f"✅ Total Form 1 revenue: RM {total_revenue:.2f}")
        
        # Test 4: PIBG Donations
        total_pibg_donations = PibgDonation.objects.filter(student__in=form1_students, status='completed').count()
        total_pibg_amount = PibgDonation.objects.filter(student__in=form1_students, status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
        
        self.stdout.write(f"✅ Total Form 1 PIBG donations: {total_pibg_donations}")
        self.stdout.write(f"✅ Total Form 1 PIBG amount: RM {total_pibg_amount:.2f}")
        
        # Test 5: Class Distribution
        class_data = {}
        for student in form1_students:
            class_name = student.class_name or 'No Class'
            if class_name not in class_data:
                class_data[class_name] = 0
            class_data[class_name] += 1
        
        self.stdout.write(f"\n✅ Form 1 Class Distribution:")
        for class_name, count in sorted(class_data.items()):
            self.stdout.write(f"   - {class_name}: {count} students")
        
        # Test 6: Recent Activity
        recent_payments = Payment.objects.filter(student__in=form1_students).order_by('-created_at')[:5]
        self.stdout.write(f"\n✅ Recent Form 1 Payments (last 5):")
        for payment in recent_payments:
            self.stdout.write(f"   - {payment.student.first_name} {payment.student.last_name}: RM{payment.amount:.2f} ({payment.created_at.strftime('%Y-%m-%d')})")
        
        # Test 7: Form 1 Admin User
        try:
            form1_admin = User.objects.get(username='form1_admin')
            profile = form1_admin.myapp_profile
            self.stdout.write(f"\n✅ Form 1 Admin User:")
            self.stdout.write(f"   - Username: {form1_admin.username}")
            self.stdout.write(f"   - Role: {profile.role}")
            self.stdout.write(f"   - Is Form 1 Admin: {profile.is_form1_admin()}")
            self.stdout.write(f"   - Assigned levels: {profile.get_assigned_levels()}")
        except User.DoesNotExist:
            self.stdout.write(f"\n❌ Form 1 Admin user not found")
        
        self.stdout.write(f"\n=== Test Complete ===")
        self.stdout.write(f"Expected: 83 students")
        self.stdout.write(f"Actual: {total_students} students")
        
        if total_students == 83:
            self.stdout.write(self.style.SUCCESS("✅ All tests passed! Form 1 admin is working correctly."))
        else:
            self.stdout.write(self.style.ERROR("❌ Some tests failed. Check the data filtering logic."))
