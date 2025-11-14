#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from myapp.models import Student, UserProfile, FeeStructure, FeeStatus
from django.contrib.auth.models import User
from datetime import date, timedelta

def fix_shakib_form_number():
    """Fix Shakib Al Hasan's form number and ensure school fees are assigned"""
    
    print("=" * 60)
    print("FIXING SHAKIB AL HASAN'S FORM NUMBER AND SCHOOL FEES")
    print("=" * 60)
    
    # Find Shakib Al Hasan
    student = Student.objects.filter(
        first_name__icontains='shakib',
        last_name__icontains='hasan'
    ).first()
    
    if not student:
        print("❌ Student Shakib Al Hasan not found!")
        return
    
    print(f"✅ Found student: {student.first_name} {student.last_name}")
    print(f"   Current Level: {student.level}")
    print(f"   Current Level Custom: {student.level_custom}")
    print(f"   Current Display Value: {student.get_level_display_value()}")
    
    # Update to Form 2 (you can change this to any form number)
    new_form_level = 'Form 2'
    print(f"\n🔧 Updating student to {new_form_level}...")
    
    # Update the student record
    student.level = 'form'
    student.level_custom = new_form_level
    student.save()
    
    print(f"✅ Updated student level to: {student.get_level_display_value()}")
    
    # Check existing fee statuses
    existing_fees = FeeStatus.objects.filter(student=student)
    print(f"\n💰 Current fee statuses: {existing_fees.count()}")
    
    # Get fee structures for Form 2
    form2_fees = FeeStructure.objects.filter(
        form__iexact=new_form_level,
        is_active=True
    )
    
    print(f"\n📚 Available fee structures for {new_form_level}:")
    for fee in form2_fees:
        print(f"   - {fee.category.name}: RM {fee.amount} ({fee.frequency})")
    
    # Remove old fee statuses that don't match Form 2
    old_fee_statuses = FeeStatus.objects.filter(student=student)
    for old_status in old_fee_statuses:
        if old_status.fee_structure.form.lower() != new_form_level.lower():
            print(f"   Removing old fee: {old_status.fee_structure.category.name}")
            old_status.delete()
    
    # Generate new fee statuses for Form 2
    generated_count = 0
    for fee_structure in form2_fees:
        # Check if fee status already exists
        existing_status = FeeStatus.objects.filter(
            student=student,
            fee_structure=fee_structure
        ).first()
        
        if not existing_status:
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
            FeeStatus.objects.create(
                student=student,
                fee_structure=fee_structure,
                amount=fee_structure.amount or 0,
                due_date=due_date,
                status='pending'
            )
            generated_count += 1
            print(f"   ✅ Created fee: {fee_structure.category.name} - RM {fee_structure.amount}")
    
    print(f"\n✅ Generated {generated_count} new fee records for {new_form_level}")
    
    # Show final fee status
    final_fees = FeeStatus.objects.filter(student=student)
    print(f"\n📊 Final fee status for {student.first_name} {student.last_name}:")
    for fee in final_fees:
        print(f"   - {fee.fee_structure.category.name}: RM {fee.amount} (Status: {fee.status})")
    
    # Show login credentials
    try:
        user_profile = student.user_profile.first()
        if user_profile:
            user = user_profile.user
            password = f"{student.student_id.lower()}123"
            print(f"\n🔑 LOGIN CREDENTIALS:")
            print(f"   Username: {user.username}")
            print(f"   Password: {password}")
            print(f"   Email: {user.email}")
        else:
            print(f"\n❌ No user account found for this student")
    except Exception as e:
        print(f"\n❌ Error checking user account: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    fix_shakib_form_number()
