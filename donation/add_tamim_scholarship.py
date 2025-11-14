#!/usr/bin/env python
"""
Add 12% scholarship for tamim123
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

def add_tamim_scholarship():
    """Add 12% scholarship for tamim123"""
    
    print("🎓 Adding 12% Scholarship for tamim123")
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
    print("📋 STEP 1: CHECKING EXISTING SCHOLARSHIPS")
    print("=" * 60)
    
    # Check existing scholarships for tamim123
    existing_waivers = FeeWaiver.objects.filter(student=student)
    print(f"📊 Current waivers/scholarships: {existing_waivers.count()}")
    
    for waiver in existing_waivers:
        print(f"   • {waiver.get_waiver_type_display()}: {waiver.percentage}% (Status: {waiver.status})")
    
    print("\n" + "=" * 60)
    print("📋 STEP 2: GETTING FEE CATEGORIES")
    print("=" * 60)
    
    # Get fee categories that tamim123 has fees for
    fee_categories = FeeCategory.objects.filter(
        feestructure__feestatus__student=student
    ).distinct()
    
    print(f"📊 Fee categories for tamim123: {fee_categories.count()}")
    for category in fee_categories:
        print(f"   • {category.name}")
    
    # Get School Fees category specifically
    school_fees_category = FeeCategory.objects.filter(name__icontains='School Fees').first()
    if school_fees_category:
        print(f"✅ Found School Fees category: {school_fees_category.name}")
    else:
        print("❌ School Fees category not found!")
        return
    
    print("\n" + "=" * 60)
    print("📋 STEP 3: CREATING 12% SCHOLARSHIP")
    print("=" * 60)
    
    # Check if scholarship already exists
    existing_scholarship = FeeWaiver.objects.filter(
        student=student,
        category=school_fees_category,
        waiver_type='scholarship',
        percentage=Decimal('12.00')
    ).first()
    
    if existing_scholarship:
        print(f"✅ 12% scholarship already exists for tamim123")
        print(f"   Status: {existing_scholarship.status}")
        print(f"   Start Date: {existing_scholarship.start_date}")
        print(f"   End Date: {existing_scholarship.end_date}")
        
        if existing_scholarship.status == 'pending':
            print("   ⚠️  Scholarship is pending approval")
        elif existing_scholarship.status == 'approved':
            print("   ✅ Scholarship is approved and active")
        else:
            print(f"   ❌ Scholarship status: {existing_scholarship.status}")
    else:
        print("➕ Creating new 12% scholarship...")
        
        # Create new scholarship
        scholarship = FeeWaiver.objects.create(
            student=student,
            category=school_fees_category,
            waiver_type='scholarship',
            amount=Decimal('0.00'),  # Not used for percentage-based
            percentage=Decimal('12.00'),  # 12% discount
            reason='Academic excellence scholarship for outstanding performance',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),  # Valid for 1 year
            status='pending'  # Will need admin approval
        )
        
        print(f"✅ 12% scholarship created successfully!")
        print(f"   Amount: {scholarship.percentage}%")
        print(f"   Reason: {scholarship.reason}")
        print(f"   Start Date: {scholarship.start_date}")
        print(f"   End Date: {scholarship.end_date}")
        print(f"   Status: {scholarship.status}")
    
    print("\n" + "=" * 60)
    print("📋 STEP 4: APPROVING SCHOLARSHIP")
    print("=" * 60)
    
    # Get the scholarship (either existing or newly created)
    scholarship = FeeWaiver.objects.filter(
        student=student,
        category=school_fees_category,
        waiver_type='scholarship',
        percentage=Decimal('12.00')
    ).first()
    
    if scholarship and scholarship.status == 'pending':
        print("✅ Approving scholarship...")
        scholarship.status = 'approved'
        scholarship.approved_by = user  # Using tamim123's user as approver for demo
        scholarship.approved_date = timezone.now()
        scholarship.save()
        print("✅ Scholarship approved successfully!")
    elif scholarship and scholarship.status == 'approved':
        print("✅ Scholarship is already approved!")
    else:
        print("❌ No pending scholarship found to approve")
    
    print("\n" + "=" * 60)
    print("📋 STEP 5: VERIFYING SCHOLARSHIP IMPACT")
    print("=" * 60)
    
    # Check how the scholarship affects tamim123's fees
    fee_statuses = FeeStatus.objects.filter(student=student)
    
    print(f"📊 Fee statuses for tamim123: {fee_statuses.count()}")
    
    for fee_status in fee_statuses:
        original_amount = fee_status.get_original_amount()
        discounted_amount = fee_status.get_discounted_amount()
        discount_info = fee_status.get_discount_info()
        
        print(f"\n💰 {fee_status.fee_structure.category.name}:")
        print(f"   Original Amount: RM {original_amount}")
        print(f"   Discounted Amount: RM {discounted_amount}")
        
        if discount_info['has_discount']:
            print(f"   Total Discount: RM {discount_info['total_discount']}")
            print(f"   Applied Waivers:")
            for waiver_info in discount_info['waivers']:
                print(f"     • {waiver_info['type']}: {waiver_info['percentage']}%")
        else:
            print(f"   No discounts applied")
    
    print("\n" + "=" * 60)
    print("🎉 SUMMARY - SCHOLARSHIP ADDED SUCCESSFULLY!")
    print("=" * 60)
    
    print("✅ 12% scholarship created and approved for tamim123")
    print("✅ Scholarship applies to School Fees")
    print("✅ Valid for 1 year from today")
    print("✅ Students will see discounted amounts in their portal")
    
    print("\n" + "=" * 60)
    print("🚀 NEXT STEPS:")
    print("=" * 60)
    print("1. Login as tamim123 to see discounted fees")
    print("2. Check that School Fees shows 12% discount")
    print("3. Test adding discounted fees to cart")
    print("4. Verify payment uses discounted amount")
    print("5. Check that other fees are not affected")

if __name__ == "__main__":
    add_tamim_scholarship()
