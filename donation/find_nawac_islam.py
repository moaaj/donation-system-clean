#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from myapp.models import Student, UserProfile
from django.contrib.auth.models import User

def find_nawac_islam():
    """Find the student Nawac Islam and their login credentials"""
    
    print("=" * 60)
    print("SEARCHING FOR NAWAC ISLAM STUDENT")
    print("=" * 60)
    
    # Search for student by name
    students = Student.objects.filter(
        first_name__icontains='nawac'
    ) | Student.objects.filter(
        last_name__icontains='islam'
    ) | Student.objects.filter(
        first_name__icontains='nawac',
        last_name__icontains='islam'
    )
    
    if not students.exists():
        print("❌ No student found with name 'Nawac Islam'")
        
        # Show all students for reference
        print("\n📋 All students in database:")
        all_students = Student.objects.all().order_by('first_name', 'last_name')
        for student in all_students:
            print(f"   - {student.first_name} {student.last_name} (ID: {student.student_id})")
        return
    
    print(f"✅ Found {students.count()} student(s) matching 'Nawac Islam':")
    
    for student in students:
        print(f"\n📚 STUDENT DETAILS:")
        print(f"   Student ID: {student.student_id}")
        print(f"   Name: {student.first_name} {student.last_name}")
        print(f"   NRIC: {student.nric}")
        print(f"   Level: {student.get_level_display_value()}")
        print(f"   Year Batch: {student.year_batch}")
        print(f"   Active: {student.is_active}")
        
        # Check if student has a user account
        try:
            user_profile = student.user_profile.first()
            if user_profile:
                user = user_profile.user
                print(f"\n👤 USER ACCOUNT DETAILS:")
                print(f"   Username: {user.username}")
                print(f"   Email: {user.email}")
                print(f"   Role: {user_profile.role}")
                print(f"   Account Created: {user.date_joined}")
                
                # Generate password based on the pattern
                password = f"{student.student_id.lower()}123"
                print(f"   Password: {password}")
                
                print(f"\n🔑 LOGIN CREDENTIALS:")
                print(f"   Username: {user.username}")
                print(f"   Password: {password}")
                
            else:
                print(f"\n❌ No user account found for this student")
                print(f"   Expected username: student_{student.student_id.lower()}")
                print(f"   Expected password: {student.student_id.lower()}123")
                
        except Exception as e:
            print(f"\n❌ Error checking user account: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    find_nawac_islam()
