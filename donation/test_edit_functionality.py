#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from myapp.models import Student

def test_edit_functionality():
    """Test the edit functionality by updating a student and checking if changes persist"""
    
    # Get the first student for testing
    student = Student.objects.first()
    if not student:
        print("No students found in database")
        return
    
    print(f"Testing edit functionality with student: {student}")
    print(f"Current data - Name: {student.first_name} {student.last_name}")
    print(f"Level: {student.level}, Level Custom: {student.level_custom}")
    print(f"Year Batch: {student.year_batch}, Active: {student.is_active}")
    
    # Store original values
    original_level = student.level
    original_level_custom = student.level_custom
    original_year_batch = student.year_batch
    original_is_active = student.is_active
    
    # Update the student
    student.level = 'form'
    student.level_custom = 'Form 3'
    student.year_batch = 2025
    student.is_active = True
    student.save()
    
    print(f"Updated student data:")
    print(f"Level: {student.level}, Level Custom: {student.level_custom}")
    print(f"Year Batch: {student.year_batch}, Active: {student.is_active}")
    
    # Refresh from database to verify changes persist
    student.refresh_from_db()
    print(f"After refresh from database:")
    print(f"Level: {student.level}, Level Custom: {student.level_custom}")
    print(f"Year Batch: {student.year_batch}, Active: {student.is_active}")
    
    # Restore original values
    student.level = original_level
    student.level_custom = original_level_custom
    student.year_batch = original_year_batch
    student.is_active = original_is_active
    student.save()
    
    print("Test completed - original values restored")

if __name__ == "__main__":
    test_edit_functionality()
