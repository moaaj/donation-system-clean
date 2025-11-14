#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from myapp.models import Student

def replace_fatima_names():
    print("=== REPLACING FATIMA NAMES WITH AMINA ===")
    
    # Find all students with first name containing 'fatima' (case insensitive)
    fatima_students = Student.objects.filter(first_name__icontains='fatima')
    
    print(f"Found {fatima_students.count()} students with name Fatima:")
    for student in fatima_students:
        print(f"  {student.student_id}: {student.first_name} {student.last_name} - Form {student.level_custom} {student.class_name}")
    
    if fatima_students.count() > 0:
        print("\nUpdating names from Fatima to Amina...")
        
        # Update all Fatima names to Amina
        updated_count = fatima_students.update(first_name='Amina')
        
        print(f"✅ Successfully updated {updated_count} students from Fatima to Amina")
        
        # Verify the changes
        print("\nVerifying changes:")
        amina_students = Student.objects.filter(first_name='Amina')
        for student in amina_students:
            print(f"  {student.student_id}: {student.first_name} {student.last_name} - Form {student.level_custom} {student.class_name}")
    else:
        print("No students with name Fatima found.")

if __name__ == '__main__':
    replace_fatima_names()
