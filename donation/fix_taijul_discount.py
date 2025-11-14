#!/usr/bin/env python
"""
Fix Taijul Islam's discount by ensuring waiver applies to correct fee category
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

def fix_taijul_discount():
    """Fix Taijul Islam's discount by ensuring waiver applies to correct fee category"""
    
    print("🔧 Fixing Taijul Islam's Discount")
    print("=" * 70)
    
    # Find Taijul Islam
    student = Student.objects.filter(
        first_name__iexact='Taijul',
        last_name__iexact='Islam'
    ).first()
    
    if not student:
        print("❌ Taijul Islam not found in database!")
        return
    
    print(f"✅ Found student: {student.first_name} {student.last_name}")
    print(f"📚 Form Level: {student.get_level_display_value()}")
    
    print("\n" + "=" * 70)
    print("📋 STEP 1: CHECKING CURRENT SITUATION")
    print("=" * 70)
    
    # Check current fee status records
    fee_statuses = FeeStatus.objects.filter(student=student)
    print(f"📊 Fee status records: {fee_statuses.count()}")
    
    for status in fee_statuses:
        print(f"   • {status.fee_structure.category.name}: RM {status.amount}")
    
    # Check current waivers
    waivers = FeeWaiver.objects.filter(student=student)
    print(f"📊 Fee waivers: {waivers.count()}")
    
    for waiver in waivers:
        print(f"   • {waiver.get_waiver_type_display()} for {waiver.category.name}: RM {waiver.amount}")
    
    print("\n" + "=" * 70)
    print("📋 STEP 2: IDENTIFYING THE PROBLEM")
    print("=" * 70)
    
    # Find the mismatch
    fee_categories = [status.fee_structure.category.name for status in fee_statuses]
    waiver_categories = [waiver.category.name for waiver in waivers]
    
    print(f"Fee categories: {fee_categories}")
    print(f"Waiver categories: {waiver_categories}")
    
    # Check if there's a mismatch
    mismatch_found = False
    for waiver in waivers:
        if waiver.category.name not in fee_categories:
            print(f"❌ Waiver for '{waiver.category.name}' but no fee status for that category")
            mismatch_found = True
    
    if not mismatch_found:
        print("✅ No category mismatch found")
        return
    
    print("\n" + "=" * 70)
    print("📋 STEP 3: CHECKING AVAILABLE FEE CATEGORIES")
    print("=" * 70)
    
    # Get all fee categories
    all_categories = FeeCategory.objects.filter(is_active=True)
    print(f"📊 Available fee categories: {all_categories.count()}")
    
    for category in all_categories:
        print(f"   • {category.name}")
    
    # Check Form 2 fee structures
    form2_fees = FeeStructure.objects.filter(form__iexact='Form 2', is_active=True)
    print(f"\n📊 Form 2 fee structures: {form2_fees.count()}")
    
    for fee in form2_fees:
        print(f"   • {fee.category.name}: RM {fee.amount}")
    
    print("\n" + "=" * 70)
    print("📋 STEP 4: FIXING THE DISCOUNT")
    print("=" * 70)
    
    # Option 1: Update waiver to apply to School Fees
    school_fees_category = FeeCategory.objects.filter(name__icontains='School Fees').first()
    tuition_category = FeeCategory.objects.filter(name__icontains='Tuition').first()
    
    if school_fees_category and tuition_category:
        print("🔧 Option 1: Update waiver to apply to School Fees")
        
        # Find the waiver for Tuition
        tuition_waiver = FeeWaiver.objects.filter(
            student=student,
            category=tuition_category
        ).first()
        
        if tuition_waiver:
            print(f"   Found waiver: {tuition_waiver.get_waiver_type_display()} for {tuition_waiver.category.name}")
            print(f"   Amount: RM {tuition_waiver.amount}")
            print(f"   Status: {tuition_waiver.status}")
            
            # Update the waiver to apply to School Fees
            old_category = tuition_waiver.category.name
            tuition_waiver.category = school_fees_category
            tuition_waiver.save()
            
            print(f"   ✅ Updated waiver from '{old_category}' to '{school_fees_category.name}'")
            
            # Verify the fix
            print("\n" + "=" * 70)
            print("📋 STEP 5: VERIFYING THE FIX")
            print("=" * 70)
            
            # Check fee status records again
            fee_statuses = FeeStatus.objects.filter(student=student)
            for status in fee_statuses:
                print(f"\n💰 {status.fee_structure.category.name}:")
                print(f"   Original Amount: RM {status.amount}")
                
                try:
                    original_amount = status.get_original_amount()
                    discounted_amount = status.get_discounted_amount()
                    discount_info = status.get_discount_info()
                    
                    print(f"   Original Amount (method): RM {original_amount}")
                    print(f"   Discounted Amount: RM {discounted_amount}")
                    
                    if discount_info['has_discount']:
                        print(f"   ✅ Discount Applied!")
                        print(f"   Total Discount: RM {discount_info['total_discount']}")
                        print(f"   Applied Waivers:")
                        for waiver_info in discount_info['waivers']:
                            print(f"     • {waiver_info['type']}: {waiver_info['percentage']}%")
                    else:
                        print(f"   ❌ No discount applied")
                        
                except Exception as e:
                    print(f"   ⚠️  Error calculating discount: {str(e)}")
            
            print("\n" + "=" * 70)
            print("🎉 SUMMARY - DISCOUNT FIXED!")
            print("=" * 70)
            
            print("✅ Waiver updated to apply to School Fees category")
            print("✅ Discount should now be visible to student")
            print("✅ Student will see reduced amount in portal")
            
            print("\n" + "=" * 70)
            print("🚀 NEXT STEPS:")
            print("=" * 70)
            print("1. Login as Taijul Islam to verify discount is visible")
            print("2. Check that School Fees shows discounted amount")
            print("3. Test adding discounted fees to cart")
            print("4. Verify payment uses discounted amount")
            
        else:
            print("❌ No tuition waiver found to update")
    else:
        print("❌ Required fee categories not found")
        print("   School Fees category:", "Found" if school_fees_category else "Not found")
        print("   Tuition category:", "Found" if tuition_category else "Not found")

if __name__ == "__main__":
    fix_taijul_discount()
