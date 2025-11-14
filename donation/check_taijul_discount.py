#!/usr/bin/env python
"""
Check Taijul Islam's fees and discounts
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

def check_taijul_discount():
    """Check Taijul Islam's fees and discounts"""
    
    print("🔍 Checking Taijul Islam's Fees and Discounts")
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
    print(f"🆔 Student ID: {student.student_id}")
    
    print("\n" + "=" * 70)
    print("📋 STEP 1: CHECKING FEE STATUS RECORDS")
    print("=" * 70)
    
    # Check fee status records
    fee_statuses = FeeStatus.objects.filter(student=student)
    print(f"📊 Fee status records: {fee_statuses.count()}")
    
    for status in fee_statuses:
        print(f"\n💰 {status.fee_structure.category.name}:")
        print(f"   Original Amount: RM {status.amount}")
        print(f"   Status: {status.status}")
        print(f"   Due Date: {status.due_date}")
        
        # Check discounted amount
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
    print("📋 STEP 2: CHECKING FEE WAIVERS/SCHOLARSHIPS")
    print("=" * 70)
    
    # Check fee waivers
    waivers = FeeWaiver.objects.filter(student=student)
    print(f"📊 Fee waivers/scholarships: {waivers.count()}")
    
    for waiver in waivers:
        print(f"\n🎓 {waiver.get_waiver_type_display()}:")
        print(f"   Category: {waiver.category.name}")
        print(f"   Status: {waiver.status}")
        print(f"   Start Date: {waiver.start_date}")
        print(f"   End Date: {waiver.end_date}")
        
        if waiver.percentage:
            print(f"   Percentage: {waiver.percentage}%")
        if waiver.amount:
            print(f"   Amount: RM {waiver.amount}")
        
        print(f"   Reason: {waiver.reason}")
        
        # Check if waiver is active
        today = date.today()
        if waiver.status == 'approved' and waiver.start_date <= today <= waiver.end_date:
            print(f"   ✅ Active and valid")
        elif waiver.status == 'pending':
            print(f"   ⚠️  Pending approval")
        elif waiver.status == 'rejected':
            print(f"   ❌ Rejected")
        else:
            print(f"   ❌ Not active (date range or status issue)")
    
    print("\n" + "=" * 70)
    print("📋 STEP 3: CHECKING WHAT STUDENT WILL SEE")
    print("=" * 70)
    
    # Check what the student will see in their portal
    pending_fees = FeeStatus.objects.filter(student=student, status='pending')
    individual_fees = IndividualStudentFee.objects.filter(student=student, is_active=True, is_paid=False)
    
    total_fees = pending_fees.count() + individual_fees.count()
    
    if total_fees == 0:
        print("❌ Student will see NO FEES in portal!")
    else:
        print(f"✅ Student will see {total_fees} fees in portal:")
        
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
    print("📋 STEP 4: CHECKING FOR POTENTIAL ISSUES")
    print("=" * 70)
    
    # Check for common issues
    issues_found = []
    
    # Check if waivers exist but are not active
    for waiver in waivers:
        today = date.today()
        if waiver.status == 'pending':
            issues_found.append(f"Waiver for {waiver.category.name} is pending approval")
        elif waiver.status == 'rejected':
            issues_found.append(f"Waiver for {waiver.category.name} was rejected")
        elif waiver.start_date > today:
            issues_found.append(f"Waiver for {waiver.category.name} hasn't started yet (starts {waiver.start_date})")
        elif waiver.end_date < today:
            issues_found.append(f"Waiver for {waiver.category.name} has expired (ended {waiver.end_date})")
    
    # Check if fee status records exist
    if fee_statuses.count() == 0:
        issues_found.append("No fee status records found - student won't see any fees")
    
    # Check if waivers exist but no fee status records
    if waivers.count() > 0 and fee_statuses.count() == 0:
        issues_found.append("Waivers exist but no fee status records - discounts won't apply")
    
    if issues_found:
        print("⚠️  Issues found:")
        for issue in issues_found:
            print(f"   • {issue}")
    else:
        print("✅ No obvious issues found")
    
    print("\n" + "=" * 70)
    print("🔧 RECOMMENDED ACTIONS:")
    print("=" * 70)
    
    if waivers.count() == 0:
        print("❌ No waivers/scholarships found for Taijul Islam")
        print("📋 Need to add waiver/scholarship via admin panel")
    else:
        print("✅ Waivers/scholarships found")
        
        # Check if any are active
        active_waivers = [w for w in waivers if w.status == 'approved' and w.start_date <= date.today() <= w.end_date]
        if active_waivers:
            print(f"✅ {len(active_waivers)} active waivers found")
        else:
            print("❌ No active waivers found")
            print("📋 Need to approve pending waivers or check date ranges")
    
    if fee_statuses.count() == 0:
        print("❌ No fee status records found")
        print("📋 Need to create fee status records for student to see fees")
    
    print("\n" + "=" * 70)
    print("🚀 NEXT STEPS:")
    print("=" * 70)
    print("1. Check if waiver is approved and active")
    print("2. Verify fee status records exist")
    print("3. Test student login to see actual display")
    print("4. Check discount calculation methods")

if __name__ == "__main__":
    check_taijul_discount()
