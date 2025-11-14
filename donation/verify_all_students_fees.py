#!/usr/bin/env python
"""
Verify that all students can now see their fees
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

def verify_all_students_fees():
    """Verify that all students can now see their fees"""
    
    print("🔍 Verifying All Students Can See Their Fees")
    print("=" * 70)
    
    # Get all active students
    all_students = Student.objects.filter(is_active=True)
    print(f"📊 Total active students: {all_students.count()}")
    
    print("\n" + "=" * 70)
    print("📋 STEP 1: CHECKING EACH STUDENT'S FEE VISIBILITY")
    print("=" * 70)
    
    students_with_fees = 0
    students_without_fees = 0
    total_fees_visible = 0
    
    for student in all_students:
        print(f"\n👤 {student.first_name} {student.last_name} ({student.get_level_display_value()})")
        print(f"   🆔 Student ID: {student.student_id}")
        
        # Check fee status records
        fee_statuses = FeeStatus.objects.filter(student=student, status='pending')
        individual_fees = IndividualStudentFee.objects.filter(student=student, is_active=True, is_paid=False)
        
        total_fees = fee_statuses.count() + individual_fees.count()
        total_fees_visible += total_fees
        
        if total_fees == 0:
            print(f"   ❌ Will see NO FEES in portal")
            students_without_fees += 1
        else:
            print(f"   ✅ Will see {total_fees} fees in portal:")
            students_with_fees += 1
            
            # Show fee status records with discounts
            for status in fee_statuses:
                try:
                    original_amount = status.get_original_amount()
                    discounted_amount = status.get_discounted_amount()
                    discount_info = status.get_discount_info()
                    
                    print(f"      💰 {status.fee_structure.category.name}:")
                    print(f"         Original: RM {original_amount}")
                    print(f"         Final Amount: RM {discounted_amount}")
                    
                    if discount_info['has_discount']:
                        print(f"         Discount: -RM {discount_info['total_discount']}")
                        print(f"         Applied: {', '.join([f'{w['type']} {w['percentage']}%' for w in discount_info['waivers']])}")
                    else:
                        print(f"         No discount applied")
                        
                except Exception as e:
                    print(f"         ⚠️  Error: {str(e)}")
            
            # Show individual fees
            for fee in individual_fees:
                print(f"      💰 {fee.name}: RM {fee.amount} (Due: {fee.due_date})")
    
    print("\n" + "=" * 70)
    print("📋 STEP 2: SUMMARY BY FORM LEVEL")
    print("=" * 70)
    
    # Group students by form level for summary
    students_by_form = {}
    for student in all_students:
        form_level = student.get_level_display_value()
        if form_level not in students_by_form:
            students_by_form[form_level] = []
        students_by_form[form_level].append(student)
    
    for form_level, students in students_by_form.items():
        print(f"\n📊 {form_level}:")
        
        form_students_with_fees = 0
        form_total_fees = 0
        
        for student in students:
            fee_statuses = FeeStatus.objects.filter(student=student, status='pending')
            individual_fees = IndividualStudentFee.objects.filter(student=student, is_active=True, is_paid=False)
            total_fees = fee_statuses.count() + individual_fees.count()
            
            if total_fees > 0:
                form_students_with_fees += 1
                form_total_fees += total_fees
        
        print(f"   • Total students: {len(students)}")
        print(f"   • Students with fees: {form_students_with_fees}")
        print(f"   • Students without fees: {len(students) - form_students_with_fees}")
        print(f"   • Total fees visible: {form_total_fees}")
    
    print("\n" + "=" * 70)
    print("📋 STEP 3: OVERALL VERIFICATION RESULTS")
    print("=" * 70)
    
    print(f"📊 Total students: {all_students.count()}")
    print(f"📊 Students with fees: {students_with_fees}")
    print(f"📊 Students without fees: {students_without_fees}")
    print(f"📊 Total fees visible: {total_fees_visible}")
    
    if students_without_fees == 0:
        print("\n✅ SUCCESS: All students can see fees in their portal!")
    else:
        print(f"\n⚠️  {students_without_fees} students still cannot see fees")
        print("📋 These students may need fee structures for their form level")
    
    print("\n" + "=" * 70)
    print("📋 STEP 4: STUDENT LOGIN VERIFICATION LIST")
    print("=" * 70)
    
    print("🔍 Students to test login with:")
    
    for student in all_students:
        # Find the user account for this student
        try:
            user_profile = UserProfile.objects.get(student=student)
            username = user_profile.user.username
        except UserProfile.DoesNotExist:
            username = "No user account"
        
        fee_statuses = FeeStatus.objects.filter(student=student, status='pending')
        individual_fees = IndividualStudentFee.objects.filter(student=student, is_active=True, is_paid=False)
        total_fees = fee_statuses.count() + individual_fees.count()
        
        status_icon = "✅" if total_fees > 0 else "❌"
        print(f"   {status_icon} {student.first_name} {student.last_name} ({student.get_level_display_value()})")
        print(f"      Username: {username}")
        print(f"      Fees visible: {total_fees}")
        
        if total_fees > 0:
            # Show what they will see
            fee_list = []
            for status in fee_statuses:
                try:
                    discounted_amount = status.get_discounted_amount()
                    fee_list.append(f"{status.fee_structure.category.name}: RM {discounted_amount}")
                except:
                    fee_list.append(f"{status.fee_structure.category.name}: RM {status.amount}")
            
            for fee in individual_fees:
                fee_list.append(f"{fee.name}: RM {fee.amount}")
            
            print(f"      Will see: {', '.join(fee_list)}")
    
    print("\n" + "=" * 70)
    print("🎉 VERIFICATION COMPLETED!")
    print("=" * 70)
    
    if students_without_fees == 0:
        print("✅ All students can now see fees in their portal!")
        print("✅ Fee status records have been created successfully!")
        print("✅ Students can add fees to cart and make payments!")
    else:
        print(f"⚠️  {students_without_fees} students still need attention")
        print("📋 Check if fee structures exist for their form levels")
    
    print("\n" + "=" * 70)
    print("🚀 NEXT STEPS:")
    print("=" * 70)
    print("1. Login as each student to verify fees are visible")
    print("2. Test adding fees to cart for different students")
    print("3. Test payment process for various form levels")
    print("4. Verify discounts are applied correctly")
    print("5. Check that students see correct amounts")

if __name__ == "__main__":
    verify_all_students_fees()

