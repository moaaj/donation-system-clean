#!/usr/bin/env python
"""
Setup fee status records for Form 2 students (Taijul Islam and Sabbir Rahman)
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

def setup_form2_fees():
    """Setup fee status records for Form 2 students"""
    
    print("🎓 Setting up Form 2 Fees for Taijul Islam and Sabbir Rahman")
    print("=" * 70)
    
    # Target students
    target_students = ['Taijul Islam', 'Sabbir Rahman']
    
    print("\n" + "=" * 70)
    print("📋 STEP 1: FINDING FORM 2 FEE STRUCTURES")
    print("=" * 70)
    
    # Get Form 2 fee structures
    form2_fees = FeeStructure.objects.filter(form__iexact='Form 2', is_active=True)
    print(f"📊 Form 2 fee structures found: {form2_fees.count()}")
    
    if form2_fees.count() == 0:
        print("❌ No Form 2 fee structures found!")
        print("⚠️  Please create fee structures for Form 2 first")
        return
    
    for fee in form2_fees:
        print(f"   ✅ {fee.category.name}: RM {fee.amount} ({fee.frequency})")
    
    print("\n" + "=" * 70)
    print("📋 STEP 2: FINDING FORM 2 STUDENTS")
    print("=" * 70)
    
    # Get Form 2 students
    form2_students = Student.objects.filter(
        level='form',
        level_custom__iexact='Form 2',
        is_active=True
    )
    
    print(f"📊 Form 2 students found: {form2_students.count()}")
    
    target_students_found = []
    for student in form2_students:
        student_name = f"{student.first_name} {student.last_name}"
        print(f"   👤 {student_name} (ID: {student.student_id})")
        
        if student_name in target_students:
            target_students_found.append(student)
            print(f"      ✅ Target student")
        else:
            print(f"      ℹ️  Other Form 2 student")
    
    if len(target_students_found) == 0:
        print("❌ No target students found!")
        return
    
    print("\n" + "=" * 70)
    print("📋 STEP 3: CREATING FEE STATUS RECORDS")
    print("=" * 70)
    
    # Create fee status records for each target student
    for student in target_students_found:
        student_name = f"{student.first_name} {student.last_name}"
        print(f"\n🎯 Setting up fees for: {student_name}")
        
        # Check existing fee status records
        existing_statuses = FeeStatus.objects.filter(student=student)
        print(f"   📊 Existing fee status records: {existing_statuses.count()}")
        
        if existing_statuses.count() > 0:
            print(f"   ✅ Student already has fee status records:")
            for status in existing_statuses:
                print(f"      • {status.fee_structure.category.name}: RM {status.amount} (Status: {status.status})")
        else:
            print(f"   ➕ Creating fee status records...")
            
            # Create fee status for each Form 2 fee structure
            created_count = 0
            for fee_structure in form2_fees:
                # Check if fee status already exists
                existing_status = FeeStatus.objects.filter(
                    student=student,
                    fee_structure=fee_structure
                ).first()
                
                if existing_status:
                    print(f"      ✅ {fee_structure.category.name}: Already exists")
                else:
                    # Create new fee status
                    fee_status = FeeStatus.objects.create(
                        student=student,
                        fee_structure=fee_structure,
                        amount=fee_structure.amount,
                        due_date=date.today() + timedelta(days=30),  # Due in 30 days
                        status='pending'
                    )
                    print(f"      ✅ {fee_structure.category.name}: RM {fee_status.amount} (Due: {fee_status.due_date})")
                    created_count += 1
            
            print(f"   🎉 Created {created_count} fee status records for {student_name}")
    
    print("\n" + "=" * 70)
    print("📋 STEP 4: VERIFICATION")
    print("=" * 70)
    
    # Verify the setup
    for student in target_students_found:
        student_name = f"{student.first_name} {student.last_name}"
        print(f"\n🔍 Verifying: {student_name}")
        
        # Check fee status records
        fee_statuses = FeeStatus.objects.filter(student=student, status='pending')
        individual_fees = IndividualStudentFee.objects.filter(student=student, is_active=True, is_paid=False)
        
        total_fees = fee_statuses.count() + individual_fees.count()
        
        if total_fees == 0:
            print(f"   ❌ Student will see NO FEES in portal!")
        else:
            print(f"   ✅ Student will see {total_fees} fees in portal:")
            
            # Show fee status records
            for status in fee_statuses:
                print(f"      • {status.fee_structure.category.name}: RM {status.amount} (Due: {status.due_date})")
            
            # Show individual fees
            for fee in individual_fees:
                print(f"      • {fee.name}: RM {fee.amount} (Due: {fee.due_date})")
    
    print("\n" + "=" * 70)
    print("🎉 SUMMARY - FORM 2 FEES SETUP COMPLETED!")
    print("=" * 70)
    
    print("✅ Fee status records created for Form 2 students")
    print("✅ Students can now see fees in their portal")
    print("✅ Fees are set to 'pending' status")
    print("✅ Due dates set to 30 days from today")
    
    print("\n" + "=" * 70)
    print("🚀 NEXT STEPS:")
    print("=" * 70)
    print("1. Login as Taijul Islam to verify fees are visible")
    print("2. Login as Sabbir Rahman to verify fees are visible")
    print("3. Test adding fees to cart")
    print("4. Test payment process")
    print("5. Check that fees show correct amounts")

if __name__ == "__main__":
    setup_form2_fees()
