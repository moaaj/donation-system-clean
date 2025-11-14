#!/usr/bin/env python
"""
Setup fee status records for all students so they can see fees for their respective form levels
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

def setup_all_students_fees():
    """Setup fee status records for all students so they can see fees for their respective form levels"""
    
    print("🎓 Setting up Fees for All Students")
    print("=" * 70)
    
    # Get all active students
    all_students = Student.objects.filter(is_active=True)
    print(f"📊 Total active students found: {all_students.count()}")
    
    # Group students by form level
    students_by_form = {}
    for student in all_students:
        form_level = student.get_level_display_value()
        if form_level not in students_by_form:
            students_by_form[form_level] = []
        students_by_form[form_level].append(student)
    
    print(f"📊 Students grouped by form level:")
    for form_level, students in students_by_form.items():
        print(f"   • {form_level}: {len(students)} students")
    
    print("\n" + "=" * 70)
    print("📋 STEP 1: CHECKING FEE STRUCTURES BY FORM LEVEL")
    print("=" * 70)
    
    # Check fee structures for each form level
    fee_structures_by_form = {}
    for form_level in students_by_form.keys():
        form_name = form_level.replace('Form ', 'Form ')  # Ensure proper format
        fee_structures = FeeStructure.objects.filter(form__iexact=form_name, is_active=True)
        fee_structures_by_form[form_level] = fee_structures
        print(f"📊 {form_level} fee structures: {fee_structures.count()}")
        for fee in fee_structures:
            print(f"   • {fee.category.name}: RM {fee.amount} ({fee.frequency})")
    
    print("\n" + "=" * 70)
    print("📋 STEP 2: CHECKING CURRENT FEE STATUS RECORDS")
    print("=" * 70)
    
    # Check current fee status records for all students
    total_fee_statuses = FeeStatus.objects.count()
    print(f"📊 Total fee status records in database: {total_fee_statuses}")
    
    students_with_fees = 0
    students_without_fees = 0
    
    for student in all_students:
        fee_statuses = FeeStatus.objects.filter(student=student)
        if fee_statuses.count() > 0:
            students_with_fees += 1
        else:
            students_without_fees += 1
    
    print(f"📊 Students with fee status records: {students_with_fees}")
    print(f"📊 Students without fee status records: {students_without_fees}")
    
    print("\n" + "=" * 70)
    print("📋 STEP 3: CREATING MISSING FEE STATUS RECORDS")
    print("=" * 70)
    
    total_created = 0
    total_students_processed = 0
    
    # Process each form level
    for form_level, students in students_by_form.items():
        print(f"\n🎯 Processing {form_level} students ({len(students)} students)")
        
        # Get fee structures for this form level
        form_name = form_level.replace('Form ', 'Form ')  # Ensure proper format
        fee_structures = FeeStructure.objects.filter(form__iexact=form_name, is_active=True)
        
        if fee_structures.count() == 0:
            print(f"   ⚠️  No fee structures found for {form_level}")
            continue
        
        form_created = 0
        
        # Process each student in this form level
        for student in students:
            student_created = 0
            
            # Check existing fee status records for this student
            existing_statuses = FeeStatus.objects.filter(student=student)
            
            # Create fee status records for each fee structure
            for fee_structure in fee_structures:
                # Check if fee status already exists
                existing_status = FeeStatus.objects.filter(
                    student=student,
                    fee_structure=fee_structure
                ).first()
                
                if existing_status:
                    # Fee status already exists
                    pass
                else:
                    # Create new fee status
                    fee_status = FeeStatus.objects.create(
                        student=student,
                        fee_structure=fee_structure,
                        amount=fee_structure.amount,
                        due_date=date.today() + timedelta(days=30),  # Due in 30 days
                        status='pending'
                    )
                    student_created += 1
            
            if student_created > 0:
                print(f"   ✅ {student.first_name} {student.last_name}: Created {student_created} fee status records")
                form_created += student_created
                total_created += student_created
            
            total_students_processed += 1
        
        print(f"   📊 Total created for {form_level}: {form_created} fee status records")
    
    print(f"\n🎉 Created {total_created} fee status records for {total_students_processed} students")
    
    print("\n" + "=" * 70)
    print("📋 STEP 4: VERIFYING THE SETUP")
    print("=" * 70)
    
    # Verify the setup
    total_fee_statuses_after = FeeStatus.objects.count()
    students_with_fees_after = 0
    students_without_fees_after = 0
    
    for student in all_students:
        fee_statuses = FeeStatus.objects.filter(student=student)
        if fee_statuses.count() > 0:
            students_with_fees_after += 1
        else:
            students_without_fees_after += 1
    
    print(f"📊 Fee status records before: {total_fee_statuses}")
    print(f"📊 Fee status records after: {total_fee_statuses_after}")
    print(f"📊 New fee status records created: {total_fee_statuses_after - total_fee_statuses}")
    
    print(f"\n📊 Students with fee status records before: {students_with_fees}")
    print(f"📊 Students with fee status records after: {students_with_fees_after}")
    print(f"📊 New students with fees: {students_with_fees_after - students_with_fees}")
    
    print(f"\n📊 Students still without fee status records: {students_without_fees_after}")
    
    if students_without_fees_after > 0:
        print("\n⚠️  Students still without fee status records:")
        for student in all_students:
            fee_statuses = FeeStatus.objects.filter(student=student)
            if fee_statuses.count() == 0:
                print(f"   • {student.first_name} {student.last_name} ({student.get_level_display_value()})")
    
    print("\n" + "=" * 70)
    print("📋 STEP 5: SUMMARY BY FORM LEVEL")
    print("=" * 70)
    
    for form_level, students in students_by_form.items():
        form_name = form_level.replace('Form ', 'Form ')
        fee_structures = FeeStructure.objects.filter(form__iexact=form_name, is_active=True)
        
        students_with_fees_count = 0
        for student in students:
            fee_statuses = FeeStatus.objects.filter(student=student)
            if fee_statuses.count() > 0:
                students_with_fees_count += 1
        
        print(f"📊 {form_level}:")
        print(f"   • Total students: {len(students)}")
        print(f"   • Fee structures: {fee_structures.count()}")
        print(f"   • Students with fees: {students_with_fees_count}")
        print(f"   • Students without fees: {len(students) - students_with_fees_count}")
    
    print("\n" + "=" * 70)
    print("🎉 SUMMARY - ALL STUDENTS FEES SETUP COMPLETED!")
    print("=" * 70)
    
    print(f"✅ Processed {total_students_processed} students")
    print(f"✅ Created {total_created} fee status records")
    print(f"✅ {students_with_fees_after} students now have fee status records")
    
    if students_without_fees_after > 0:
        print(f"⚠️  {students_without_fees_after} students still need fee structures for their form level")
    
    print("\n" + "=" * 70)
    print("🚀 NEXT STEPS:")
    print("=" * 70)
    print("1. Login as different students to verify fees are visible")
    print("2. Check that students can see fees for their form level")
    print("3. Test payment process for various students")
    print("4. Verify discounts are applied correctly")
    print("5. Create fee structures for any missing form levels")

if __name__ == "__main__":
    setup_all_students_fees()
