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

def check_students_without_form_numbers():
    """Check for students without proper form numbers"""
    
    print("=" * 60)
    print("CHECKING STUDENTS WITHOUT FORM NUMBERS")
    print("=" * 60)
    
    # Find students with level='form' but no level_custom
    students_without_form = Student.objects.filter(
        level='form',
        level_custom__isnull=True
    ) | Student.objects.filter(
        level='form',
        level_custom=''
    )
    
    print(f"Found {students_without_form.count()} students with level='form' but no form number:")
    
    for student in students_without_form:
        print(f"\n📚 Student: {student.first_name} {student.last_name}")
        print(f"   Student ID: {student.student_id}")
        print(f"   Level: {student.level}")
        print(f"   Level Custom: {student.level_custom}")
        print(f"   Display Value: {student.get_level_display_value()}")
        
        # Check if they have user account
        try:
            user_profile = student.user_profile.first()
            if user_profile:
                print(f"   Username: {user_profile.user.username}")
            else:
                print(f"   ❌ No user account")
        except:
            print(f"   ❌ Error checking user account")
    
    # Find students with level='form' and level_custom set
    students_with_form = Student.objects.filter(
        level='form',
        level_custom__isnull=False
    ).exclude(level_custom='')
    
    print(f"\n✅ Found {students_with_form.count()} students with proper form numbers:")
    
    for student in students_with_form:
        print(f"   - {student.first_name} {student.last_name}: {student.level_custom}")
    
    # Show all students for reference
    print(f"\n📋 All students in database:")
    all_students = Student.objects.all().order_by('first_name', 'last_name')
    for student in all_students:
        level_display = student.get_level_display_value()
        print(f"   - {student.first_name} {student.last_name}: {level_display}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    check_students_without_form_numbers()
