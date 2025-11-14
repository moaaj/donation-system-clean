#!/usr/bin/env python
"""
Check tamim123's Form 3 fees and ensure they can see fees when logged in
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

from myapp.models import Student, UserProfile, FeeCategory, FeeStructure, FeeStatus, IndividualStudentFee, FeeWaiver, Payment
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta

def check_tamim_form3_fees():
    """Check tamim123's Form 3 fees and ensure they can see fees when logged in"""
    
    print("🔍 Checking tamim123's Form 3 Fees")
    print("=" * 70)
    
    # Find tamim123 user and student
    user = User.objects.filter(username='tamim123').first()
    if not user:
        print("❌ User 'tamim123' not found!")
        return
    
    student = user.myapp_profile.student
    print(f"✅ Found student: {student.first_name} {student.last_name}")
    print(f"📚 Form Level: {student.get_level_display_value()}")
    print(f"🆔 Student ID: {student.student_id}")
    
    print("\n" + "=" * 70)
    print("📋 STEP 1: CHECKING FORM 3 FEE STRUCTURES")
    print("=" * 70)
    
    # Check Form 3 fee structures
    form3_fees = FeeStructure.objects.filter(form__iexact='Form 3', is_active=True)
    print(f"📊 Form 3 fee structures: {form3_fees.count()}")
    
    for fee in form3_fees:
        print(f"   • {fee.category.name}: RM {fee.amount} ({fee.frequency})")
    
    print("\n" + "=" * 70)
    print("📋 STEP 2: CHECKING TAMIM123'S FEE STATUS RECORDS")
    print("=" * 70)
    
    # Check fee status records for tamim123
    fee_statuses = FeeStatus.objects.filter(student=student)
    print(f"📊 Fee status records for tamim123: {fee_statuses.count()}")
    
    for status in fee_statuses:
        print(f"   • {status.fee_structure.category.name}: RM {status.amount} (Status: {status.status}, Due: {status.due_date})")
    
    print("\n" + "=" * 70)
    print("📋 STEP 3: CHECKING WHAT TAMIM123 WILL SEE")
    print("=" * 70)
    
    # Check what tamim123 will see in their portal
    pending_fees = FeeStatus.objects.filter(student=student, status='pending')
    individual_fees = IndividualStudentFee.objects.filter(student=student, is_active=True, is_paid=False)
    
    total_fees = pending_fees.count() + individual_fees.count()
    
    if total_fees == 0:
        print("❌ tamim123 will see NO FEES in portal!")
        print("⚠️  This means no fee status records exist for tamim123")
    else:
        print(f"✅ tamim123 will see {total_fees} fees in portal:")
        
        # Show fee status records with discounts
        for status in pending_fees:
            try:
                original_amount = status.get_original_amount()
                discounted_amount = status.get_discounted_amount()
                discount_info = status.get_discount_info()
                
                print(f"\n💰 {status.fee_structure.category.name}:")
                print(f"   Original: RM {original_amount}")
                print(f"   Final Amount: RM {discounted_amount}")
                
                if discount_info['has_discount']:
                    print(f"   Discount: -RM {discount_info['total_discount']}")
                    print(f"   Applied: {', '.join([f'{w['type']} {w['percentage']}%' for w in discount_info['waivers']])}")
                else:
                    print(f"   No discount applied")
                    
            except Exception as e:
                print(f"   ⚠️  Error: {str(e)}")
        
        # Show individual fees
        for fee in individual_fees:
            print(f"\n💰 {fee.name}: RM {fee.amount} (Due: {fee.due_date})")
    
    print("\n" + "=" * 70)
    print("📋 STEP 4: IDENTIFYING THE PROBLEM")
    print("=" * 70)
    
    # Check if there's a mismatch between fee structures and fee status records
    form3_categories = [fee.category.name for fee in form3_fees]
    status_categories = [status.fee_structure.category.name for status in fee_statuses]
    
    print(f"Form 3 fee categories: {form3_categories}")
    print(f"tamim123's fee status categories: {status_categories}")
    
    # Find missing fee status records
    missing_categories = []
    for category in form3_categories:
        if category not in status_categories:
            missing_categories.append(category)
    
    if missing_categories:
        print(f"❌ Missing fee status records for categories: {missing_categories}")
        print("📋 Need to create fee status records for tamim123 to see these fees")
    else:
        print("✅ All Form 3 fee categories have fee status records")
    
    print("\n" + "=" * 70)
    print("🔧 RECOMMENDED ACTIONS:")
    print("=" * 70)
    
    if form3_fees.count() == 0:
        print("❌ No Form 3 fee structures found!")
        print("📋 Need to create fee structures for Form 3 first")
    else:
        print("✅ Form 3 fee structures exist")
        
        if fee_statuses.count() == 0:
            print("❌ No fee status records for tamim123")
            print("📋 Need to create fee status records for tamim123 to see fees")
        elif missing_categories:
            print(f"❌ Missing fee status records for {len(missing_categories)} categories")
            print("📋 Need to create fee status records for missing categories")
        else:
            print("✅ All fee status records exist")
            print("📋 tamim123 should be able to see fees in portal")
    
    print("\n" + "=" * 70)
    print("🚀 NEXT STEPS:")
    print("=" * 70)
    print("1. Create fee status records for tamim123 if missing")
    print("2. Verify tamim123 can see fees in portal")
    print("3. Test payment process")
    print("4. Check discount functionality if applicable")

if __name__ == "__main__":
    check_tamim_form3_fees()
