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

def test_add_student_functionality():
    """Test the add student functionality with automatic user account creation"""
    
    # Test data
    test_student_data = {
        'student_id': 'TEST001',
        'nric': 'T123456-78-9012',
        'first_name': 'Test',
        'last_name': 'Student',
        'level': 'form',
        'level_custom': 'Form 3',
        'year_batch': 2025,
        'is_active': True
    }
    
    print("Testing add student functionality with automatic user account creation...")
    
    # Check if test student already exists
    existing_student = Student.objects.filter(student_id='TEST001').first()
    if existing_student:
        print(f"Test student already exists: {existing_student}")
        # Clean up existing test data
        if hasattr(existing_student, 'user_profile') and existing_student.user_profile.first():
            user_profile = existing_student.user_profile.first()
            user = user_profile.user
            user_profile.delete()
            user.delete()
        existing_student.delete()
        print("Cleaned up existing test data")
    
    # Create test student
    student = Student.objects.create(**test_student_data)
    print(f"Created test student: {student}")
    
    # Test automatic user account creation
    try:
        # Generate username from student ID
        username = f"student_{student.student_id.lower()}"
        password = f"{student.student_id.lower()}123"
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            print(f"User account already exists for username: {username}")
        else:
            # Create user account
            user = User.objects.create_user(
                username=username,
                email=f"{username}@school.com",
                password=password,
                first_name=student.first_name,
                last_name=student.last_name
            )
            
            # Create user profile
            user_profile = UserProfile.objects.create(
                user=user,
                role='student',
                student=student
            )
            
            print(f"User account created successfully!")
            print(f"Username: {username}")
            print(f"Password: {password}")
            print(f"Email: {user.email}")
            print(f"User Profile Role: {user_profile.role}")
            
            # Test authentication
            from django.contrib.auth import authenticate
            authenticated_user = authenticate(username=username, password=password)
            if authenticated_user:
                print("✅ Authentication test passed!")
            else:
                print("❌ Authentication test failed!")
                
    except Exception as e:
        print(f"Error creating user account: {e}")
    
    # Clean up test data
    try:
        if hasattr(student, 'user_profile') and student.user_profile.first():
            user_profile = student.user_profile.first()
            user = user_profile.user
            user_profile.delete()
            user.delete()
        student.delete()
        print("Test data cleaned up successfully")
    except Exception as e:
        print(f"Error cleaning up test data: {e}")
    
    print("Test completed!")

if __name__ == "__main__":
    test_add_student_functionality()
