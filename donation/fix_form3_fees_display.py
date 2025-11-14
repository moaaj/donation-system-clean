#!/usr/bin/env python3
"""
Fix Form 3 Fees Display Issue

This script fixes the issue where Form 3 school fees are not showing on student pages.
The problem occurs when fee structures exist but students don't have corresponding FeeStatus records.

Usage:
    python fix_form3_fees_display.py
"""

import os
import sys
import django
from datetime import date, timedelta

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from myapp.models import Student, FeeStructure, FeeStatus

def fix_form3_fees_display():
    """
    Fix Form 3 fees display by creating missing FeeStatus records
    """
    print("🔧 Fixing Form 3 Fees Display Issue")
    print("=" * 50)
    
    # Get all Form 3 students
    form3_students = Student.objects.filter(
        is_active=True,
        level='form',
        level_custom__iexact='Form 3'
    )
    
    print(f"📊 Found {form3_students.count()} Form 3 students")
    
    if form3_students.count() == 0:
        print("❌ No Form 3 students found!")
        return
    
    # Get all active Form 3 fee structures
    form3_fee_structures = FeeStructure.objects.filter(
        form__iexact='Form 3',
        is_active=True
    )
    
    print(f"📊 Found {form3_fee_structures.count()} Form 3 fee structures")
    
    if form3_fee_structures.count() == 0:
        print("❌ No Form 3 fee structures found!")
        return
    
    # Display existing fee structures
    print("\n📋 Form 3 Fee Structures:")
    for fee_structure in form3_fee_structures:
        print(f"   • {fee_structure.category.name}: RM {fee_structure.amount} ({fee_structure.frequency})")
    
    total_created = 0
    students_processed = 0
    
    # Process each student
    for student in form3_students:
        print(f"\n👤 Processing student: {student.first_name} {student.last_name} ({student.student_id})")
        
        student_created = 0
        
        # Check existing fee status records
        existing_statuses = FeeStatus.objects.filter(student=student)
        print(f"   📊 Existing fee status records: {existing_statuses.count()}")
        
        # Create missing fee status records
        for fee_structure in form3_fee_structures:
            # Check if fee status already exists
            existing_status = FeeStatus.objects.filter(
                student=student,
                fee_structure=fee_structure
            ).first()
            
            if existing_status:
                print(f"   ✅ {fee_structure.category.name}: Already exists (Status: {existing_status.status})")
            else:
                # Calculate due date based on frequency
                if fee_structure.frequency == 'yearly':
                    due_date = date.today() + timedelta(days=30)
                elif fee_structure.frequency == 'termly':
                    due_date = date.today() + timedelta(days=90)
                elif fee_structure.frequency == 'monthly':
                    due_date = date.today() + timedelta(days=30)
                else:
                    due_date = date.today() + timedelta(days=30)
                
                # Create fee status
                fee_status = FeeStatus.objects.create(
                    student=student,
                    fee_structure=fee_structure,
                    amount=fee_structure.amount or 0,
                    due_date=due_date,
                    status='pending'
                )
                
                print(f"   ➕ {fee_structure.category.name}: RM {fee_status.amount} (Due: {fee_status.due_date})")
                student_created += 1
        
        if student_created > 0:
            print(f"   🎉 Created {student_created} fee status records for {student.first_name}")
            total_created += student_created
        
        students_processed += 1
    
    print("\n" + "=" * 50)
    print("📋 SUMMARY")
    print("=" * 50)
    print(f"✅ Students processed: {students_processed}")
    print(f"✅ Fee status records created: {total_created}")
    
    if total_created > 0:
        print(f"\n🎉 SUCCESS! Form 3 students can now see their fees in the student portal.")
        print(f"   • {total_created} fee status records were created")
        print(f"   • All Form 3 students now have pending fees visible")
    else:
        print(f"\n✅ All Form 3 students already have their fee status records.")
    
    # Verify the fix
    print(f"\n🔍 VERIFICATION:")
    for student in form3_students:
        fee_statuses = FeeStatus.objects.filter(student=student)
        print(f"   • {student.first_name} {student.last_name}: {fee_statuses.count()} fee status records")
        for status in fee_statuses:
            print(f"     - {status.fee_structure.category.name}: RM {status.amount} ({status.status})")

if __name__ == "__main__":
    fix_form3_fees_display()
