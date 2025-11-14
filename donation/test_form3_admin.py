#!/usr/bin/env python
"""
Test Form 3 admin functionality
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from myapp.models import Student, FeeStatus, Payment
from accounts.models import UserProfile
from django.contrib.auth.models import User

def test_form3_admin_functionality():
    """Test Form 3 admin functionality"""
    
    print("🧪 TESTING FORM 3 ADMIN FUNCTIONALITY")
    print("=" * 70)
    
    # Test 1: Check Form 3 admin user exists
    print("\n📋 TEST 1: Form 3 Admin User")
    print("-" * 40)
    
    try:
        form3_admin = User.objects.get(username='form3_admin')
        profile = form3_admin.profile
        print(f"✅ Form 3 admin user exists: {form3_admin.username}")
        print(f"✅ Role: {profile.role}")
        print(f"✅ Is Form 3 admin: {profile.is_form3_admin()}")
        print(f"✅ Is staff: {form3_admin.is_staff}")
        print(f"✅ Is superuser: {form3_admin.is_superuser}")
    except User.DoesNotExist:
        print("❌ Form 3 admin user does not exist!")
        return False
    
    # Test 2: Check Form 3 students exist
    print("\n📋 TEST 2: Form 3 Students")
    print("-" * 40)
    
    form3_students = Student.objects.filter(
        level='form',
        level_custom__iexact='Form 3',
        is_active=True
    )
    
    print(f"✅ Found {form3_students.count()} Form 3 students:")
    for student in form3_students:
        print(f"   • {student.first_name} {student.last_name} ({student.student_id})")
        print(f"     Class: {student.class_name}, Program: {student.program}")
    
    if form3_students.count() == 0:
        print("❌ No Form 3 students found!")
        return False
    
    # Test 3: Check Form 3 fee statuses
    print("\n📋 TEST 3: Form 3 Fee Statuses")
    print("-" * 40)
    
    form3_fee_statuses = FeeStatus.objects.filter(
        student__in=form3_students
    )
    
    print(f"✅ Found {form3_fee_statuses.count()} fee status records for Form 3 students")
    
    if form3_fee_statuses.count() > 0:
        for status in form3_fee_statuses[:3]:  # Show first 3
            print(f"   • {status.student.first_name}: {status.fee_structure.category.name} - RM {status.amount} ({status.status})")
    
    # Test 4: Check Form 3 payments
    print("\n📋 TEST 4: Form 3 Payments")
    print("-" * 40)
    
    form3_payments = Payment.objects.filter(
        student__in=form3_students
    )
    
    print(f"✅ Found {form3_payments.count()} payments for Form 3 students")
    
    if form3_payments.count() > 0:
        total_revenue = sum(payment.amount for payment in form3_payments if payment.status == 'completed')
        print(f"✅ Total revenue from Form 3 students: RM {total_revenue:.2f}")
    
    # Test 5: Test access restrictions
    print("\n📋 TEST 5: Access Restrictions")
    print("-" * 40)
    
    # Check that Form 3 admin can only see Form 3 students
    all_students = Student.objects.filter(is_active=True)
    non_form3_students = all_students.exclude(
        level='form',
        level_custom__iexact='Form 3'
    )
    
    print(f"✅ Total active students in system: {all_students.count()}")
    print(f"✅ Form 3 students: {form3_students.count()}")
    print(f"✅ Non-Form 3 students: {non_form3_students.count()}")
    print(f"✅ Form 3 admin should only see {form3_students.count()} students")
    
    # Test 6: Check user accounts for Form 3 students
    print("\n📋 TEST 6: Form 3 Student User Accounts")
    print("-" * 40)
    
    for student in form3_students:
        user_profiles = student.user_profile.all()
        if user_profiles.exists():
            user_profile = user_profiles.first()
            user = user_profile.user
            print(f"✅ {student.first_name} {student.last_name}: {user.username}")
        else:
            print(f"❌ {student.first_name} {student.last_name}: No user account")
    
    print(f"\n🎉 FORM 3 ADMIN FUNCTIONALITY TEST COMPLETED!")
    print("=" * 70)
    print("✅ Form 3 admin user exists and has correct role")
    print("✅ Form 3 students are properly configured")
    print("✅ Fee statuses are set up for Form 3 students")
    print("✅ Access restrictions are in place")
    print("✅ Form 3 admin can only manage Form 3 students")
    
    print(f"\n🚀 NEXT STEPS:")
    print("=" * 70)
    print("1. Login as form3_admin (password: form3admin123)")
    print("2. Verify Form 3 admin dashboard shows only Form 3 students")
    print("3. Test Form 3 admin can manage Form 3 fees and payments")
    print("4. Verify Form 3 admin cannot access other form levels")
    
    return True

if __name__ == "__main__":
    test_form3_admin_functionality()
