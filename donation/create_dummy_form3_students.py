#!/usr/bin/env python
"""
Create dummy Form 3 students for testing Form 3 admin functionality
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

from myapp.models import Student, UserProfile, FeeCategory, FeeStructure, FeeStatus
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta

def create_dummy_form3_students():
    """Create dummy Form 3 students for testing"""
    
    print("🎓 CREATING DUMMY FORM 3 STUDENTS")
    print("=" * 70)
    
    # Clean up any existing dummy Form 3 students
    print("🧹 Cleaning up existing dummy Form 3 students...")
    dummy_students = Student.objects.filter(
        student_id__startswith='F3DUMMY',
        level='form',
        level_custom__iexact='Form 3'
    )
    
    for student in dummy_students:
        # Delete associated user accounts
        user_profiles = student.user_profile.all()
        for user_profile in user_profiles:
            if user_profile.user:
                user_profile.user.delete()
        student.delete()
    
    print(f"✅ Cleaned up {dummy_students.count()} existing dummy students")
    
    # Dummy Form 3 students data
    dummy_students_data = [
        {
            'student_id': 'F3DUMMY001',
            'nric': 'F30012345678',
            'first_name': 'Ahmad',
            'last_name': 'Hassan',
            'level': 'form',
            'level_custom': 'Form 3',
            'year_batch': 2025,
            'class_name': 'Form 3A',
            'program': 'Science Stream',
            'is_active': True
        },
        {
            'student_id': 'F3DUMMY002',
            'nric': 'F30012345679',
            'first_name': 'Siti',
            'last_name': 'Rahman',
            'level': 'form',
            'level_custom': 'Form 3',
            'year_batch': 2025,
            'class_name': 'Form 3B',
            'program': 'Arts Stream',
            'is_active': True
        },
        {
            'student_id': 'F3DUMMY003',
            'nric': 'F30012345680',
            'first_name': 'Muhammad',
            'last_name': 'Ali',
            'level': 'form',
            'level_custom': 'Form 3',
            'year_batch': 2025,
            'class_name': 'Form 3A',
            'program': 'Science Stream',
            'is_active': True
        },
        {
            'student_id': 'F3DUMMY004',
            'nric': 'F30012345681',
            'first_name': 'Fatimah',
            'last_name': 'Ibrahim',
            'level': 'form',
            'level_custom': 'Form 3',
            'year_batch': 2025,
            'class_name': 'Form 3C',
            'program': 'Commerce Stream',
            'is_active': True
        },
        {
            'student_id': 'F3DUMMY005',
            'nric': 'F30012345682',
            'first_name': 'Omar',
            'last_name': 'Yusuf',
            'level': 'form',
            'level_custom': 'Form 3',
            'year_batch': 2025,
            'class_name': 'Form 3B',
            'program': 'Arts Stream',
            'is_active': True
        }
    ]
    
    print(f"\n📚 Creating {len(dummy_students_data)} dummy Form 3 students...")
    
    created_students = []
    success_count = 0
    error_count = 0
    
    for i, student_data in enumerate(dummy_students_data, 1):
        try:
            print(f"\n📝 Creating student {i}: {student_data['first_name']} {student_data['last_name']}")
            
            # Create student
            student = Student.objects.create(**student_data)
            print(f"   ✅ Student created: {student.student_id}")
            
            # Create user account
            username = f"f3_{student.student_id.lower()}"
            password = f"{student.student_id.lower()}123"
            
            user = User.objects.create_user(
                username=username,
                email=f"{username}@school.com",
                password=password,
                first_name=student.first_name,
                last_name=student.last_name
            )
            
            user_profile = UserProfile.objects.create(
                user=user,
                role='student',
                student=student
            )
            
            print(f"   ✅ User account created - Username: {username}, Password: {password}")
            
            created_students.append({
                'student': student,
                'username': username,
                'password': password
            })
            
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ Error creating student {i}: {str(e)}")
            error_count += 1
    
    print(f"\n📊 SUMMARY:")
    print(f"   ✅ Successfully created: {success_count} students")
    print(f"   ❌ Errors: {error_count} students")
    
    if created_students:
        print(f"\n🎯 CREATED FORM 3 STUDENTS:")
        print("=" * 70)
        for student_info in created_students:
            student = student_info['student']
            print(f"📚 {student.first_name} {student.last_name}")
            print(f"   🆔 Student ID: {student.student_id}")
            print(f"   👤 Username: {student_info['username']}")
            print(f"   🔑 Password: {student_info['password']}")
            print(f"   📚 Class: {student.class_name}")
            print(f"   📖 Program: {student.program}")
            print()
    
    # Setup fee status records for Form 3 students
    print("💰 SETTING UP FEE STATUS RECORDS")
    print("=" * 70)
    
    # Get Form 3 fee structures
    form3_fee_structures = FeeStructure.objects.filter(
        form__iexact='Form 3',
        is_active=True
    )
    
    print(f"📊 Found {form3_fee_structures.count()} Form 3 fee structures")
    
    if form3_fee_structures.count() == 0:
        print("⚠️  No Form 3 fee structures found!")
        print("   Creating basic Form 3 fee structure...")
        
        # Create a basic fee category for Form 3
        fee_category, created = FeeCategory.objects.get_or_create(
            name='Form 3 School Fees',
            defaults={
                'description': 'Standard school fees for Form 3 students',
                'category_type': 'general',
                'is_active': True
            }
        )
        
        # Create a basic fee structure for Form 3
        fee_structure = FeeStructure.objects.create(
            category=fee_category,
            form='Form 3',
            amount=Decimal('2000.00'),
            frequency='termly',
            is_active=True
        )
        
        print(f"   ✅ Created Form 3 fee structure: {fee_structure.category.name} - RM {fee_structure.amount}")
        form3_fee_structures = [fee_structure]
    
    # Create fee status records for each student
    fee_status_created = 0
    for student_info in created_students:
        student = student_info['student']
        
        for fee_structure in form3_fee_structures:
            # Check if fee status already exists
            existing_status = FeeStatus.objects.filter(
                student=student,
                fee_structure=fee_structure
            ).first()
            
            if not existing_status:
                fee_status = FeeStatus.objects.create(
                    student=student,
                    fee_structure=fee_structure,
                    amount=fee_structure.amount,
                    due_date=date.today() + timedelta(days=30),
                    status='pending'
                )
                fee_status_created += 1
                print(f"   ✅ Created fee status for {student.first_name} {student.last_name}: {fee_structure.category.name}")
    
    print(f"\n🎉 DUMMY FORM 3 STUDENTS CREATION COMPLETED!")
    print("=" * 70)
    print(f"✅ Created {success_count} Form 3 students")
    print(f"✅ Created {fee_status_created} fee status records")
    print(f"✅ All students have user accounts for login")
    print(f"✅ All students have pending fees visible in portal")
    
    print(f"\n🚀 NEXT STEPS:")
    print("=" * 70)
    print("1. Create a Form 3 admin user account")
    print("2. Test Form 3 admin functionality")
    print("3. Login as students to verify fees are visible")
    print("4. Test Form 3 admin can manage these students")
    
    return created_students

if __name__ == "__main__":
    create_dummy_form3_students()
