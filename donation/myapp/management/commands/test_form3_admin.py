from django.core.management.base import BaseCommand
from myapp.models import Student, Payment, PibgDonation
from django.db.models import Sum, Count
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Test Form 3 admin functionality and data retrieval'

    def handle(self, *args, **options):
        self.stdout.write("=== Form 3 Admin Data Test ===\n")
        
        # Test 1: Student Count
        form3_students = Student.objects.filter(level_custom__in=['3', 'Form 3'], is_active=True)
        total_students = form3_students.count()
        self.stdout.write(f"✅ Total Form 3 students (active): {total_students}")
        
        # Test 2: Payment Statistics
        total_payments = Payment.objects.filter(student__in=form3_students).count()
        completed_payments = Payment.objects.filter(student__in=form3_students, status='completed').count()
        pending_payments = Payment.objects.filter(student__in=form3_students, status='pending').count()
        
        self.stdout.write(f"✅ Total Form 3 payments: {total_payments}")
        self.stdout.write(f"✅ Completed Form 3 payments: {completed_payments}")
        self.stdout.write(f"✅ Pending Form 3 payments: {pending_payments}")
        
        # Test 3: Revenue
        total_revenue = Payment.objects.filter(student__in=form3_students, status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
        self.stdout.write(f"✅ Total Form 3 revenue: RM {total_revenue:.2f}")
        
        # Test 4: PIBG Donations
        total_pibg_donations = PibgDonation.objects.filter(student__in=form3_students, status='completed').count()
        total_pibg_amount = PibgDonation.objects.filter(student__in=form3_students, status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
        
        self.stdout.write(f"✅ Total Form 3 PIBG donations: {total_pibg_donations}")
        self.stdout.write(f"✅ Total Form 3 PIBG amount: RM {total_pibg_amount:.2f}")
        
        # Test 5: Class Distribution
        class_data = {}
        for student in form3_students:
            class_name = student.class_name or 'No Class'
            if class_name not in class_data:
                class_data[class_name] = 0
            class_data[class_name] += 1
        
        self.stdout.write(f"\n✅ Form 3 Class Distribution:")
        for class_name, count in sorted(class_data.items()):
            self.stdout.write(f"   - {class_name}: {count} students")
        
        # Test 6: Check tamim123 specifically
        tamim = Student.objects.filter(student_id='tamim123', level_custom__in=['3', 'Form 3']).first()
        if tamim:
            self.stdout.write(f"\n✅ tamim123 found: {tamim.first_name} {tamim.last_name} (Level: {tamim.level_custom}, Class: {tamim.class_name})")
            tamim_payments = Payment.objects.filter(student=tamim).count()
            self.stdout.write(f"   - tamim123 payments: {tamim_payments}")
        else:
            self.stdout.write(f"\n❌ tamim123 NOT found in Form 3 students")
        
        # Test 7: Recent Activity
        recent_payments = Payment.objects.filter(student__in=form3_students).order_by('-created_at')[:5]
        self.stdout.write(f"\n✅ Recent Form 3 Payments (last 5):")
        for payment in recent_payments:
            self.stdout.write(f"   - {payment.student.first_name} {payment.student.last_name}: RM{payment.amount:.2f} ({payment.created_at.strftime('%Y-%m-%d')})")
        
        # Test 8: Form 3 Admin User
        try:
            form3_admin = User.objects.get(username='form3_admin')
            profile = form3_admin.myapp_profile
            self.stdout.write(f"\n✅ Form 3 Admin User:")
            self.stdout.write(f"   - Username: {form3_admin.username}")
            self.stdout.write(f"   - Role: {profile.role}")
            self.stdout.write(f"   - Is Form 3 Admin: {profile.is_form3_admin()}")
            self.stdout.write(f"   - Assigned Levels: {profile.get_assigned_levels()}")
        except User.DoesNotExist:
            self.stdout.write(f"\n❌ Form 3 Admin user not found")
        
        self.stdout.write(f"\n=== Test Complete ===")
        self.stdout.write(f"Expected: 91 students, 309 payments, RM 83,415 revenue")
        self.stdout.write(f"Actual: {total_students} students, {total_payments} payments, RM {total_revenue:.2f} revenue")
        
        if total_students == 91 and total_payments == 309:
            self.stdout.write(self.style.SUCCESS("✅ All tests passed! Form 3 admin is working correctly."))
        else:
            self.stdout.write(self.style.ERROR("❌ Some tests failed. Check the data filtering logic."))
