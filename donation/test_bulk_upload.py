#!/usr/bin/env python
import os
import sys
import django
import pandas as pd
from openpyxl import Workbook

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from myapp.models import Student

def create_test_file():
    """Create a test Excel file for bulk upload"""
    wb = Workbook()
    ws = wb.active
    ws.title = "Students Template"
    
    # Add headers
    headers = ['student_id', 'nric', 'first_name', 'last_name', 'year_batch', 'class_name', 'program', 'level', 'level_custom']
    ws.append(headers)
    
    # Add test data
    test_data = [
        ['TEST001', '123456-78-9012', 'John', 'Doe', '2024', 'Class A', 'Science', 'form', ''],
        ['TEST002', '123456-78-9013', 'Jane', 'Smith', '2024', 'Class B', 'Arts', 'year', ''],
        ['TEST003', '123456-78-9014', 'Bob', 'Johnson', '2024', 'Class C', 'Commerce', 'standard', ''],
    ]
    
    for row in test_data:
        ws.append(row)
    
    # Save the file
    filename = 'test_students.xlsx'
    wb.save(filename)
    print(f"Test file created: {filename}")
    return filename

def test_student_creation():
    """Test creating a student manually"""
    try:
        # Delete existing test students
        Student.objects.filter(student_id__startswith='TEST').delete()
        
        # Create a test student
        student = Student(
            student_id='TEST001',
            nric='123456-78-9012',
            first_name='John',
            last_name='Doe',
            year_batch=2024,
            class_name='Class A',
            program='Science',
            level='form',
            is_active=True
        )
        student.save()
        
        print(f"Test student created: {student}")
        
        # Check if student exists
        student_check = Student.objects.filter(student_id='TEST001').first()
        if student_check:
            print(f"Student found in database: {student_check}")
            print(f"Class: {student_check.class_name}")
            print(f"Program: {student_check.program}")
            print(f"Level: {student_check.level}")
        else:
            print("Student not found in database!")
            
    except Exception as e:
        print(f"Error creating test student: {e}")

def check_existing_students():
    """Check existing students in the database"""
    students = Student.objects.all()
    print(f"Total students in database: {students.count()}")
    
    for student in students[:5]:
        print(f"Student: {student.student_id} - {student.first_name} {student.last_name}")
        print(f"  Class: {student.class_name}")
        print(f"  Program: {student.program}")
        print(f"  Level: {student.level}")
        print(f"  Active: {student.is_active}")

if __name__ == '__main__':
    print("=== Testing Bulk Upload Functionality ===")
    
    # Check existing students
    print("\n1. Checking existing students:")
    check_existing_students()
    
    # Create test file
    print("\n2. Creating test file:")
    create_test_file()
    
    # Test student creation
    print("\n3. Testing student creation:")
    test_student_creation()
    
    print("\n=== Test Complete ===")
