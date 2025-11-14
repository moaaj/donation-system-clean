#!/usr/bin/env python
"""
Check tamim123's fee status records and ensure School Fees are visible
"""

import os
import sys
import django
from decimal import Decimal

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from myapp.models import Student, UserProfile, FeeCategory, FeeStructure, FeeStatus, IndividualStudentFee, Payment
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta

def check_tamim_fee_status():
    """Check tamim123's fee status and ensure School Fees are visible"""
    
    print("🔍 Checking tamim123's Fee Status Records")
    print("=" * 60)
    
    # Get tamim123 user and student
    user = User.objects.filter(username='tamim123').first()
    if not user:
        print("❌ User 'tamim123' not found!")
        return
    
    student = user.myapp_profile.student
    print(f"✅ Found student: {student.first_name} {student.last_name}")
    print(f"📚 Form Level: {student.get_level_display_value()}")
    
    print("\n" + "=" * 60)
    print("📋 CURRENT FEE STATUS RECORDS FOR TAMIM:")
    print("=" * 60)
    
    # Check existing fee statuses for tamim123
    existing_statuses = FeeStatus.objects.filter(student=student)
    print(f"📊 Current fee statuses: {existing_statuses.count()}")
    
    if existing_statuses.count() == 0:
        print("❌ No fee status records found! This means tamim123 won't see any fees.")
    else:
        for status in existing_statuses:
            print(f"   • {status.fee_structure.category.name}: RM {status.amount} (Status: {status.status}, Due: {status.due_date})")
    
    print("\n" + "=" * 60)
    print("📚 FORM 3 FEE STRUCTURES AVAILABLE:")
    print("=" * 60)
    
    # Check Form 3 fee structures
    form3_fees = FeeStructure.objects.filter(form__iexact='Form 3', is_active=True)
    print(f"📊 Form 3 fee structures: {form3_fees.count()}")
    
    for fee in form3_fees:
        status = FeeStatus.objects.filter(student=student, fee_structure=fee).first()
        if status:
            print(f"   ✅ {fee.category.name}: RM {status.amount} (Status: {status.status}, Due: {status.due_date})")
        else:
            print(f"   ❌ {fee.category.name}: RM {fee.amount} ({fee.frequency}) - NO STATUS RECORD")
    
    print("\n" + "=" * 60)
    print("🎯 WHAT TAMIM WILL SEE IN STUDENT PORTAL:")
    print("=" * 60)
    
    # Check what tamim will actually see
    fee_statuses = FeeStatus.objects.filter(student=student, status='pending')
    individual_fees = IndividualStudentFee.objects.filter(student=student, is_active=True, is_paid=False)
    
    if fee_statuses.count() == 0 and individual_fees.count() == 0:
        print("❌ tamim123 will see NO FEES in the student portal!")
        print("   This is because there are no fee status records created.")
    else:
        print("📋 Fee Status Records (Form-based fees):")
        for status in fee_statuses:
            print(f"   • {status.fee_structure.category.name}: RM {status.amount} (Due: {status.due_date})")
        
        print("\n📋 Individual Student Fees:")
        for fee in individual_fees:
            print(f"   • {fee.name}: RM {fee.amount} (Due: {fee.due_date})")
    
    print("\n" + "=" * 60)
    print("🔧 RECOMMENDED ACTIONS:")
    print("=" * 60)
    
    # Check if School Fees status record exists
    school_fees_structure = FeeStructure.objects.filter(
        category__name__icontains='School Fees',
        form__iexact='Form 3',
        is_active=True
    ).first()
    
    if school_fees_structure:
        school_fees_status = FeeStatus.objects.filter(
            student=student,
            fee_structure=school_fees_structure
        ).first()
        
        if not school_fees_status:
            print("❌ School Fees status record missing!")
            print("   Need to create FeeStatus record for School Fees")
        else:
            print("✅ School Fees status record exists")
            print(f"   Amount: RM {school_fees_status.amount}")
            print(f"   Status: {school_fees_status.status}")
            print(f"   Due Date: {school_fees_status.due_date}")
    
    # Check for Sports Fees to remove
    sports_fees_structure = FeeStructure.objects.filter(
        category__name__icontains='Sports',
        form__iexact='Form 3',
        is_active=True
    ).first()
    
    if sports_fees_structure:
        sports_fees_status = FeeStatus.objects.filter(
            student=student,
            fee_structure=sports_fees_structure
        ).first()
        
        if sports_fees_status:
            print("❌ Sports Fees status record exists - needs to be removed")
        else:
            print("✅ Sports Fees status record doesn't exist")
    
    print("\n" + "=" * 60)
    print("🚀 NEXT STEPS:")
    print("=" * 60)
    print("1. Create FeeStatus record for School Fees (if missing)")
    print("2. Remove Sports Fees status record (if exists)")
    print("3. Test login as tamim123 to verify fees are visible")

if __name__ == "__main__":
    check_tamim_fee_status()
