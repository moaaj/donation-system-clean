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

def test_bulk_student_creation():
    """Test bulk student creation functionality"""
    
    print("=" * 60)
    print("TESTING BULK STUDENT CREATION FUNCTIONALITY")
    print("=" * 60)
    
    # Test data for bulk creation
    test_students = [
        {
            'student_id': 'BULK001',
            'nric': '12345678901',
            'first_name': 'Bulk',
            'last_name': 'Student 1',
            'year_batch': 2024,
            'level': 'form',
            'level_custom': 'Form 1',
            'class_name': 'Test Class A',
            'program': 'Science',
            'is_active': True
        },
        {
            'student_id': 'BULK002',
            'nric': '12345678902',
            'first_name': 'Bulk',
            'last_name': 'Student 2',
            'year_batch': 2024,
            'level': 'form',
            'level_custom': 'Form 2',
            'class_name': 'Test Class B',
            'program': 'Arts',
            'is_active': True
        },
        {
            'student_id': 'BULK003',
            'nric': '12345678903',
            'first_name': 'Bulk',
            'last_name': 'Student 3',
            'year_batch': 2024,
            'level': 'form',
            'level_custom': '',  # Should auto-assign Form 1
            'class_name': 'Test Class C',
            'program': 'Commerce',
            'is_active': True
        }
    ]
    
    success_count = 0
    error_count = 0
    
    for i, student_data in enumerate(test_students, 1):
        try:
            print(f"\n📚 Creating student {i}: {student_data['first_name']} {student_data['last_name']}")
            
            # Check if student already exists
            if Student.objects.filter(student_id=student_data['student_id']).exists():
                print(f"   ⚠️  Student {student_data['student_id']} already exists, skipping...")
                continue
            
            # Auto-assign form number if level is 'form' but no form number is selected
            if student_data['level'] == 'form' and not student_data['level_custom']:
                student_data['level_custom'] = 'Form 1'
                print(f"   🔧 Auto-assigned form number: {student_data['level_custom']}")
            
            # Create student
            student = Student(**student_data)
            student.save()
            print(f"   ✅ Student created successfully")
            
            # Automatically create user account
            try:
                username = f"student_{student.student_id.lower()}"
                if User.objects.filter(username=username).exists():
                    print(f"   ⚠️  User account already exists: {username}")
                else:
                    password = f"{student.student_id.lower()}123"
                    user = User.objects.create_user(
                        username=username,
                        email=f"{username}@school.com",
                        password=password,
                        first_name=student.first_name,
                        last_name=student.last_name
                    )
                    UserProfile.objects.create(
                        user=user,
                        role='student',
                        student=student
                    )
                    print(f"   ✅ User account created - Username: {username}, Password: {password}")
            except Exception as e:
                print(f"   ❌ Error creating user account: {e}")
            
            # Generate fee statuses if student has a form level
            if student.level == 'form' and student.level_custom:
                try:
                    form_fees = FeeStructure.objects.filter(
                        form__iexact=student.level_custom,
                        is_active=True
                    )
                    
                    fee_count = 0
                    for fee_structure in form_fees:
                        existing_status = FeeStatus.objects.filter(
                            student=student,
                            fee_structure=fee_structure
                        ).first()
                        
                        if not existing_status:
                            if fee_structure.frequency == 'yearly':
                                due_date = date.today() + timedelta(days=30)
                            elif fee_structure.frequency == 'termly':
                                due_date = date.today() + timedelta(days=90)
                            elif fee_structure.frequency == 'monthly':
                                due_date = date.today() + timedelta(days=30)
                            else:
                                due_date = date.today() + timedelta(days=30)
                            
                            FeeStatus.objects.create(
                                student=student,
                                fee_structure=fee_structure,
                                amount=fee_structure.amount or 0,
                                due_date=due_date,
                                status='pending'
                            )
                            fee_count += 1
                            print(f"   ✅ Created fee: {fee_structure.category.name} - RM {fee_structure.amount}")
                    
                    if fee_count > 0:
                        print(f"   📊 Total fees created: {fee_count}")
                    else:
                        print(f"   ℹ️  No fees created (no fee structures found for {student.level_custom})")
                        
                except Exception as e:
                    print(f"   ❌ Error creating fee statuses: {e}")
            
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ Error creating student: {e}")
            error_count += 1
    
    print(f"\n📊 BULK CREATION RESULTS:")
    print(f"   ✅ Successfully created: {success_count} students")
    print(f"   ❌ Errors: {error_count} students")
    
    # Show all bulk test students
    bulk_students = Student.objects.filter(student_id__startswith='BULK')
    print(f"\n📋 All bulk test students:")
    for student in bulk_students:
        level_display = student.get_level_display_value()
        user_profile = student.user_profile.first()
        username = user_profile.user.username if user_profile else "No user account"
        fees = FeeStatus.objects.filter(student=student).count()
        print(f"   - {student.first_name} {student.last_name}: {level_display} | User: {username} | Fees: {fees}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_bulk_student_creation()
