#!/usr/bin/env python
"""
Fix tamim123's fees: Remove Sports Fees and ensure School Fees are visible
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

def fix_tamim_fees():
    """Remove Sports Fees and ensure School Fees are visible for tamim123"""
    
    print("🔧 Fixing tamim123's Fees")
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
    print("🗑️ STEP 1: REMOVING SPORTS FEES")
    print("=" * 60)
    
    # Find and remove Sports Fees status record
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
            print(f"🗑️ Removing Sports Fees status record...")
            sports_fees_status.delete()
            print(f"✅ Sports Fees status record removed successfully")
        else:
            print(f"✅ Sports Fees status record doesn't exist")
    else:
        print(f"✅ Sports Fees structure not found")
    
    print("\n" + "=" * 60)
    print("➕ STEP 2: CREATING SCHOOL FEES STATUS RECORD")
    print("=" * 60)
    
    # Find School Fees structure
    school_fees_structure = FeeStructure.objects.filter(
        category__name__icontains='School Fees',
        form__iexact='Form 3',
        is_active=True
    ).first()
    
    if school_fees_structure:
        print(f"📚 Found School Fees structure: {school_fees_structure.category.name}")
        print(f"   Amount: RM {school_fees_structure.amount}")
        print(f"   Frequency: {school_fees_structure.frequency}")
        
        # Check if status record already exists
        existing_status = FeeStatus.objects.filter(
            student=student,
            fee_structure=school_fees_structure
        ).first()
        
        if existing_status:
            print(f"✅ School Fees status record already exists")
            print(f"   Amount: RM {existing_status.amount}")
            print(f"   Status: {existing_status.status}")
            print(f"   Due Date: {existing_status.due_date}")
        else:
            print(f"➕ Creating School Fees status record...")
            
            # Create new fee status record
            new_fee_status = FeeStatus.objects.create(
                student=student,
                fee_structure=school_fees_structure,
                amount=school_fees_structure.amount,
                due_date=date.today() + timedelta(days=30),  # Due in 30 days
                status='pending'
            )
            
            print(f"✅ School Fees status record created successfully")
            print(f"   Amount: RM {new_fee_status.amount}")
            print(f"   Status: {new_fee_status.status}")
            print(f"   Due Date: {new_fee_status.due_date}")
    else:
        print(f"❌ School Fees structure not found!")
        return
    
    print("\n" + "=" * 60)
    print("🎯 STEP 3: VERIFICATION")
    print("=" * 60)
    
    # Check final status
    fee_statuses = FeeStatus.objects.filter(student=student, status='pending')
    individual_fees = IndividualStudentFee.objects.filter(student=student, is_active=True, is_paid=False)
    
    print(f"📊 Final fee statuses: {fee_statuses.count()}")
    for status in fee_statuses:
        print(f"   ✅ {status.fee_structure.category.name}: RM {status.amount} (Due: {status.due_date})")
    
    print(f"\n📊 Final individual fees: {individual_fees.count()}")
    for fee in individual_fees:
        print(f"   ✅ {fee.name}: RM {fee.amount} (Due: {fee.due_date})")
    
    print("\n" + "=" * 60)
    print("🎉 SUMMARY - WHAT TAMIM123 WILL SEE NOW:")
    print("=" * 60)
    
    total_fees = fee_statuses.count() + individual_fees.count()
    if total_fees > 0:
        print(f"✅ tamim123 will see {total_fees} fees in the student portal:")
        
        print("\n📋 Form-based Fees:")
        for status in fee_statuses:
            print(f"   • {status.fee_structure.category.name}: RM {status.amount} (Due: {status.due_date})")
        
        print("\n📋 Individual Fees:")
        for fee in individual_fees:
            print(f"   • {fee.name}: RM {fee.amount} (Due: {fee.due_date})")
        
        print(f"\n💰 Total fees visible: {total_fees}")
    else:
        print("❌ tamim123 will see NO FEES in the student portal!")
    
    print("\n" + "=" * 60)
    print("🚀 NEXT STEPS:")
    print("=" * 60)
    print("1. Login as tamim123 to verify fees are visible")
    print("2. Test adding fees to cart")
    print("3. Test payment process")
    print("4. Verify discount functionality works")

if __name__ == "__main__":
    fix_tamim_fees()
