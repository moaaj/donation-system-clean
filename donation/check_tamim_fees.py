#!/usr/bin/env python
"""
Check Tamim's student information and fees
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from myapp.models import Student, FeeStructure, FeeStatus, Payment
from django.contrib.auth.models import User

def check_tamim_fees():
    """Check Tamim's student information and fees"""
    print("=" * 60)
    print("CHECKING TAMIM'S STUDENT INFORMATION AND FEES")
    print("=" * 60)
    
    # Get Tamim's user and student record
    user = User.objects.filter(username='tamim123').first()
    if not user:
        print("❌ User 'tamim123' not found!")
        return
    
    print(f"✅ User found: {user.username}")
    
    # Check if user has a student profile
    if not hasattr(user, 'myapp_profile'):
        print("❌ User 'tamim123' does not have a student profile!")
        return
    
    if user.myapp_profile.role != 'student':
        print(f"❌ User 'tamim123' is not a student (role: {user.myapp_profile.role})")
        return
    
    student = user.myapp_profile.student
    print(f"✅ Student found: {student.first_name} {student.last_name}")
    
    # Show student details
    print(f"\n📚 STUDENT DETAILS:")
    print(f"   Student ID: {student.student_id}")
    print(f"   NRIC: {student.nric}")
    print(f"   Class: {student.class_name}")
    print(f"   Program: {student.program}")
    print(f"   Level: {student.level}")
    print(f"   Level Custom: {student.level_custom}")
    print(f"   Form Level: {student.get_level_display_value()}")
    print(f"   Year Batch: {student.year_batch}")
    print(f"   Active: {student.is_active}")
    
    # Check which form level this student should be in
    student_level = student.get_level_display_value()
    print(f"\n🎯 FORM LEVEL ANALYSIS:")
    print(f"   Current Level: {student_level}")
    
    if 'Form' in student_level:
        print(f"   ✅ Student is properly assigned to {student_level}")
    else:
        print(f"   ⚠️  Student is not assigned to a specific form level")
        print(f"   Current level: {student_level}")
        print(f"   To assign to Form 3, set:")
        print(f"   - level = 'form'")
        print(f"   - level_custom = 'Form 3'")
    
    # Check available fee structures for this student's level
    print(f"\n💰 AVAILABLE FEES FOR {student_level}:")
    
    if 'Form' in student_level:
        # Get fee structures for this student's form level
        available_fees = FeeStructure.objects.filter(
            form__iexact=student_level,
            is_active=True
        ).select_related('category')
        
        if available_fees.exists():
            for fee in available_fees:
                amount_display = f"RM {fee.amount}" if fee.amount else "Not set"
                if fee.frequency == 'monthly' and fee.total_amount and fee.monthly_duration:
                    monthly_amount = fee.get_monthly_amount()
                    amount_display = f"RM {fee.total_amount} over {fee.monthly_duration} months (Monthly: RM {monthly_amount})"
                
                print(f"   {fee.category.name}: {amount_display} ({fee.frequency})")
        else:
            print(f"   ❌ No fee structures found for {student_level}")
    else:
        print(f"   ❌ Cannot determine fees - student not assigned to a form level")
    
    # Check existing fee statuses for this student
    print(f"\n📋 EXISTING FEE STATUSES:")
    fee_statuses = FeeStatus.objects.filter(student=student).select_related('fee_structure', 'fee_structure__category')
    
    if fee_statuses.exists():
        for status in fee_statuses:
            print(f"   {status.fee_structure.category.name} - {status.fee_structure.form}:")
            print(f"     Amount: RM {status.amount}")
            print(f"     Status: {status.status}")
            print(f"     Due Date: {status.due_date}")
    else:
        print(f"   ℹ️  No fee statuses found for this student")
    
    # Check payments for this student
    print(f"\n💳 PAYMENT HISTORY:")
    payments = Payment.objects.filter(student=student).order_by('-payment_date')
    
    if payments.exists():
        for payment in payments[:5]:  # Show last 5 payments
            print(f"   {payment.payment_date}: RM {payment.amount} - {payment.status}")
    else:
        print(f"   ℹ️  No payment history found")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    if 'Form' not in student_level:
        print(f"   1. Assign student to a specific form level (e.g., Form 3)")
        print(f"   2. Update student.level = 'form'")
        print(f"   3. Update student.level_custom = 'Form 3'")
        print(f"   4. Then fees will automatically appear for that form level")
    else:
        print(f"   1. Student is properly assigned to {student_level}")
        print(f"   2. Fees should be visible in the student portal")
        print(f"   3. Check if fee structures exist for {student_level}")
    
    print(f"\n" + "=" * 60)

if __name__ == '__main__':
    try:
        check_tamim_fees()
    except Exception as e:
        print(f"Error during check: {str(e)}")
        import traceback
        traceback.print_exc()
