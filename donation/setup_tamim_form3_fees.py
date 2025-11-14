#!/usr/bin/env python
"""
Setup fee status records for tamim123 so they can see Form 3 fees
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

def setup_tamim_form3_fees():
    """Setup fee status records for tamim123 so they can see Form 3 fees"""
    
    print("🎓 Setting up Form 3 Fees for tamim123")
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
    print("📋 STEP 1: FINDING FORM 3 FEE STRUCTURES")
    print("=" * 70)
    
    # Get Form 3 fee structures
    form3_fees = FeeStructure.objects.filter(form__iexact='Form 3', is_active=True)
    print(f"📊 Form 3 fee structures found: {form3_fees.count()}")
    
    if form3_fees.count() == 0:
        print("❌ No Form 3 fee structures found!")
        print("⚠️  Please create fee structures for Form 3 first")
        return
    
    for fee in form3_fees:
        print(f"   ✅ {fee.category.name}: RM {fee.amount} ({fee.frequency})")
    
    print("\n" + "=" * 70)
    print("📋 STEP 2: CHECKING CURRENT FEE STATUS RECORDS")
    print("=" * 70)
    
    # Check current fee status records
    existing_statuses = FeeStatus.objects.filter(student=student)
    print(f"📊 Current fee status records: {existing_statuses.count()}")
    
    for status in existing_statuses:
        print(f"   • {status.fee_structure.category.name}: RM {status.amount} (Status: {status.status})")
    
    print("\n" + "=" * 70)
    print("📋 STEP 3: CREATING MISSING FEE STATUS RECORDS")
    print("=" * 70)
    
    # Create fee status records for each Form 3 fee structure
    created_count = 0
    for fee_structure in form3_fees:
        # Check if fee status already exists
        existing_status = FeeStatus.objects.filter(
            student=student,
            fee_structure=fee_structure
        ).first()
        
        if existing_status:
            print(f"   ✅ {fee_structure.category.name}: Already exists")
        else:
            # Create new fee status
            fee_status = FeeStatus.objects.create(
                student=student,
                fee_structure=fee_structure,
                amount=fee_structure.amount,
                due_date=date.today() + timedelta(days=30),  # Due in 30 days
                status='pending'
            )
            print(f"   ✅ {fee_structure.category.name}: RM {fee_status.amount} (Due: {fee_status.due_date})")
            created_count += 1
    
    print(f"\n🎉 Created {created_count} fee status records for tamim123")
    
    print("\n" + "=" * 70)
    print("📋 STEP 4: VERIFYING THE SETUP")
    print("=" * 70)
    
    # Verify the setup
    fee_statuses = FeeStatus.objects.filter(student=student, status='pending')
    individual_fees = IndividualStudentFee.objects.filter(student=student, is_active=True, is_paid=False)
    
    total_fees = fee_statuses.count() + individual_fees.count()
    
    if total_fees == 0:
        print("❌ tamim123 will see NO FEES in portal!")
    else:
        print(f"✅ tamim123 will see {total_fees} fees in portal:")
        
        # Show fee status records with discounts
        for status in fee_statuses:
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
    print("🎉 SUMMARY - FORM 3 FEES SETUP COMPLETED!")
    print("=" * 70)
    
    print("✅ Fee status records created for tamim123")
    print("✅ tamim123 can now see Form 3 fees in their portal")
    print("✅ Fees are set to 'pending' status")
    print("✅ Due dates set to 30 days from today")
    
    print("\n" + "=" * 70)
    print("🚀 NEXT STEPS:")
    print("=" * 70)
    print("1. Login as tamim123 to verify Form 3 fees are visible")
    print("2. Check that School Fees shows correct amount")
    print("3. Test adding fees to cart")
    print("4. Test payment process")
    print("5. Check that discounts are applied correctly")

if __name__ == "__main__":
    setup_tamim_form3_fees()
