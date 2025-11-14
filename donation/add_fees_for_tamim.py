#!/usr/bin/env python
"""
Add fees for tamim123 - Comprehensive Guide
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

def add_fees_for_tamim():
    """Demonstrate all ways to add fees for tamim123"""
    
    print("🎯 Adding Fees for tamim123 - Comprehensive Guide")
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
    print("📋 METHOD 1: Add Individual Student Fees")
    print("=" * 60)
    print("Individual fees are perfect for:")
    print("• One-time charges (overtime, late fees)")
    print("• Penalties (demerit fees)")
    print("• Special charges specific to this student")
    print("• Equipment fees, field trip fees, etc.")
    
    # Check existing individual fees
    existing_individual_fees = IndividualStudentFee.objects.filter(student=student, is_active=True)
    print(f"\n📊 Current individual fees: {existing_individual_fees.count()}")
    for fee in existing_individual_fees:
        print(f"   • {fee.name}: RM {fee.amount} (Due: {fee.due_date})")
    
    # Add a new individual fee
    print(f"\n➕ Adding new individual fee...")
    
    # Get or create a category for individual fees
    category, created = FeeCategory.objects.get_or_create(
        name='Special Fees',
        defaults={
            'description': 'Special fees for individual students',
            'category_type': 'individual'
        }
    )
    
    # Create a new individual fee
    new_fee = IndividualStudentFee.objects.create(
        student=student,
        category=category,
        name='Library Fine',
        description='Late return of library books',
        amount=Decimal('15.00'),
        due_date=date.today() + timedelta(days=7),
        is_paid=False,
        is_active=True,
        created_by=user
    )
    
    print(f"✅ Added individual fee: {new_fee.name} - RM {new_fee.amount}")
    
    print("\n" + "=" * 60)
    print("📋 METHOD 2: Create New Fee Structure for Form 3")
    print("=" * 60)
    print("Fee structures apply to ALL students in Form 3:")
    print("• All Form 3 students will see this fee")
    print("• Ensures fairness and consistency")
    print("• Good for new fee categories (sports, activities, etc.)")
    
    # Check existing fee structures for Form 3
    form3_fees = FeeStructure.objects.filter(form__iexact='Form 3', is_active=True)
    print(f"\n📊 Current Form 3 fee structures: {form3_fees.count()}")
    for fee in form3_fees:
        print(f"   • {fee.category.name}: RM {fee.amount} ({fee.frequency})")
    
    # Add a new fee structure for Form 3
    print(f"\n➕ Adding new fee structure for Form 3...")
    
    # Get or create a category
    sports_category, created = FeeCategory.objects.get_or_create(
        name='Sports Fees',
        defaults={
            'description': 'Sports and physical education fees',
            'category_type': 'general'
        }
    )
    
    # Create new fee structure
    new_fee_structure = FeeStructure.objects.create(
        category=sports_category,
        form='Form 3',
        amount=Decimal('200.00'),
        frequency='yearly',
        is_active=True
    )
    
    print(f"✅ Added fee structure: {new_fee_structure.category.name} - RM {new_fee_structure.amount} ({new_fee_structure.frequency})")
    print(f"   This fee will appear for ALL Form 3 students, including tamim123")
    
    print("\n" + "=" * 60)
    print("📋 METHOD 3: Create Fee Status Records")
    print("=" * 60)
    print("Fee status records create payment obligations:")
    print("• Links fee structures to specific students")
    print("• Sets due dates and payment status")
    print("• Required for students to see fees in their portal")
    
    # Check existing fee statuses for tamim123
    existing_statuses = FeeStatus.objects.filter(student=student)
    print(f"\n📊 Current fee statuses: {existing_statuses.count()}")
    for status in existing_statuses:
        print(f"   • {status.fee_structure.category.name}: RM {status.amount} (Status: {status.status}, Due: {status.due_date})")
    
    # Create a new fee status for the sports fee
    print(f"\n➕ Creating fee status for sports fee...")
    
    new_fee_status = FeeStatus.objects.create(
        student=student,
        fee_structure=new_fee_structure,
        amount=new_fee_structure.amount,
        due_date=date.today() + timedelta(days=30),
        status='pending'
    )
    
    print(f"✅ Created fee status: {new_fee_status.fee_structure.category.name} - RM {new_fee_status.amount} (Due: {new_fee_status.due_date})")
    
    print("\n" + "=" * 60)
    print("📋 METHOD 4: Using Management Commands")
    print("=" * 60)
    print("Pre-built commands for common fee types:")
    print("• python manage.py add_overtime_fee")
    print("• python manage.py setup_form_based_fees")
    print("• Custom commands for specific fee types")
    
    print("\n" + "=" * 60)
    print("📋 METHOD 5: Web Interface")
    print("=" * 60)
    print("Admin can add fees through web interface:")
    print("1. Login as admin")
    print("2. Go to 'Individual Student Fees'")
    print("3. Click 'Add New Fee'")
    print("4. Select tamim123 as student")
    print("5. Fill in fee details")
    print("6. Save")
    
    print("\n" + "=" * 60)
    print("🎯 SUMMARY - What tamim123 will see now:")
    print("=" * 60)
    
    # Show all fees tamim123 will see
    print("📚 Form 3 Fee Structures:")
    form3_fees = FeeStructure.objects.filter(form__iexact='Form 3', is_active=True)
    for fee in form3_fees:
        status = FeeStatus.objects.filter(student=student, fee_structure=fee).first()
        if status:
            print(f"   • {fee.category.name}: RM {status.amount} (Due: {status.due_date}, Status: {status.status})")
        else:
            print(f"   • {fee.category.name}: RM {fee.amount} ({fee.frequency}) - No status record yet")
    
    print("\n📋 Individual Student Fees:")
    individual_fees = IndividualStudentFee.objects.filter(student=student, is_active=True, is_paid=False)
    for fee in individual_fees:
        print(f"   • {fee.name}: RM {fee.amount} (Due: {fee.due_date})")
    
    print("\n" + "=" * 60)
    print("💡 RECOMMENDATIONS:")
    print("=" * 60)
    print("✅ Use Individual Student Fees for:")
    print("   • One-time charges (overtime, fines)")
    print("   • Student-specific fees")
    print("   • Penalties or special charges")
    
    print("\n✅ Use Fee Structures for:")
    print("   • Standard fees for all students in a form")
    print("   • Tuition, examination, sports fees")
    print("   • Any fee that applies to multiple students")
    
    print("\n✅ Always create Fee Status records:")
    print("   • Required for students to see fees")
    print("   • Sets due dates and payment tracking")
    print("   • Enables payment processing")
    
    print("\n" + "=" * 60)
    print("🚀 NEXT STEPS:")
    print("=" * 60)
    print("1. Login as tamim123 to see the new fees")
    print("2. Add fees to cart and test payment")
    print("3. Check that discounts work with new fees")
    print("4. Monitor payment status and receipts")

if __name__ == "__main__":
    add_fees_for_tamim()
