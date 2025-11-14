#!/usr/bin/env python
"""
Check Form 2 students (Taijul Islam and Sabbir Rahman) and their fee visibility
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

def check_form2_students():
    """Check Form 2 students and their fee visibility"""
    
    print("🔍 Checking Form 2 Students - Taijul Islam and Sabbir Rahman")
    print("=" * 70)
    
    # Find Form 2 students
    form2_students = Student.objects.filter(
        level='form',
        level_custom__iexact='Form 2',
        is_active=True
    )
    
    print(f"📊 Total Form 2 students found: {form2_students.count()}")
    
    # Check specific students
    target_students = ['Taijul Islam', 'Sabbir Rahman']
    
    for student in form2_students:
        print(f"\n👤 Student: {student.first_name} {student.last_name}")
        print(f"   Student ID: {student.student_id}")
        print(f"   Form Level: {student.get_level_display_value()}")
        print(f"   Active: {student.is_active}")
        
        # Check if this is one of our target students
        full_name = f"{student.first_name} {student.last_name}"
        if full_name in target_students:
            print(f"   ✅ Target student found!")
        else:
            print(f"   ℹ️  Other Form 2 student")
    
    print("\n" + "=" * 70)
    print("📋 STEP 1: CHECKING FORM 2 FEE STRUCTURES")
    print("=" * 70)
    
    # Check Form 2 fee structures
    form2_fees = FeeStructure.objects.filter(form__iexact='Form 2', is_active=True)
    print(f"📊 Form 2 fee structures: {form2_fees.count()}")
    
    for fee in form2_fees:
        print(f"   • {fee.category.name}: RM {fee.amount} ({fee.frequency})")
    
    print("\n" + "=" * 70)
    print("📋 STEP 2: CHECKING FEE STATUS RECORDS")
    print("=" * 70)
    
    # Check fee status records for Form 2 students
    form2_fee_statuses = FeeStatus.objects.filter(
        student__level='form',
        student__level_custom__iexact='Form 2'
    )
    
    print(f"📊 Fee status records for Form 2 students: {form2_fee_statuses.count()}")
    
    for status in form2_fee_statuses:
        student_name = f"{status.student.first_name} {status.student.last_name}"
        print(f"   • {student_name}: {status.fee_structure.category.name} - RM {status.amount} (Status: {status.status})")
    
    print("\n" + "=" * 70)
    print("📋 STEP 3: CHECKING TARGET STUDENTS SPECIFICALLY")
    print("=" * 70)
    
    # Check each target student
    for target_name in target_students:
        print(f"\n🎯 Checking: {target_name}")
        
        # Find the student
        first_name, last_name = target_name.split(' ', 1)
        student = Student.objects.filter(
            first_name__iexact=first_name,
            last_name__iexact=last_name,
            level='form',
            level_custom__iexact='Form 2'
        ).first()
        
        if student:
            print(f"   ✅ Student found: {student.first_name} {student.last_name}")
            print(f"   📚 Form Level: {student.get_level_display_value()}")
            print(f"   🆔 Student ID: {student.student_id}")
            
            # Check fee status records
            fee_statuses = FeeStatus.objects.filter(student=student)
            print(f"   📊 Fee status records: {fee_statuses.count()}")
            
            if fee_statuses.count() == 0:
                print(f"   ❌ No fee status records found!")
                print(f"   ⚠️  Student will NOT see any fees in portal")
            else:
                print(f"   ✅ Fee status records found:")
                for status in fee_statuses:
                    print(f"      • {status.fee_structure.category.name}: RM {status.amount} (Status: {status.status}, Due: {status.due_date})")
            
            # Check individual fees
            individual_fees = IndividualStudentFee.objects.filter(student=student, is_active=True, is_paid=False)
            print(f"   📊 Individual fees: {individual_fees.count()}")
            
            for fee in individual_fees:
                print(f"      • {fee.name}: RM {fee.amount} (Due: {fee.due_date})")
            
            # Check what student will see
            pending_fees = FeeStatus.objects.filter(student=student, status='pending')
            total_fees = pending_fees.count() + individual_fees.count()
            
            if total_fees == 0:
                print(f"   ❌ Student will see NO FEES in portal!")
            else:
                print(f"   ✅ Student will see {total_fees} fees in portal")
                
        else:
            print(f"   ❌ Student NOT found in database!")
            print(f"   ⚠️  Need to create student record first")
    
    print("\n" + "=" * 70)
    print("🔧 RECOMMENDED ACTIONS:")
    print("=" * 70)
    
    # Check if we need to create fee status records
    form2_fees = FeeStructure.objects.filter(form__iexact='Form 2', is_active=True)
    form2_students = Student.objects.filter(level='form', level_custom__iexact='Form 2', is_active=True)
    
    if form2_fees.count() > 0 and form2_students.count() > 0:
        print("✅ Form 2 fee structures exist")
        print("✅ Form 2 students exist")
        print("📋 Need to create fee status records for students to see fees")
        
        for student in form2_students:
            student_name = f"{student.first_name} {student.last_name}"
            fee_statuses = FeeStatus.objects.filter(student=student)
            
            if fee_statuses.count() == 0:
                print(f"   ❌ {student_name}: No fee status records - needs creation")
            else:
                print(f"   ✅ {student_name}: Has {fee_statuses.count()} fee status records")
    else:
        if form2_fees.count() == 0:
            print("❌ No Form 2 fee structures found!")
        if form2_students.count() == 0:
            print("❌ No Form 2 students found!")
    
    print("\n" + "=" * 70)
    print("🚀 NEXT STEPS:")
    print("=" * 70)
    print("1. Create fee status records for Form 2 students")
    print("2. Verify students can see fees in portal")
    print("3. Test payment process")
    print("4. Check discount functionality if applicable")

if __name__ == "__main__":
    check_form2_students()
