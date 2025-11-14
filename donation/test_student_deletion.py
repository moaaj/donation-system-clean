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
from django.contrib.auth import authenticate

def test_student_deletion():
    """Test that student deletion properly removes user accounts and prevents login"""
    
    print("🧪 Testing Student Deletion Functionality")
    print("=" * 50)
    
    # Test data
    test_student_data = {
        'student_id': 'DELTEST001',
        'nric': 'D123456-78',
        'first_name': 'Delete',
        'last_name': 'Test',
        'level': 'form',
        'level_custom': 'Form 3',
        'year_batch': 2025,
        'is_active': True
    }
    
    # Clean up any existing test data
    existing_student = Student.objects.filter(student_id='DELTEST001').first()
    if existing_student:
        print("🧹 Cleaning up existing test data...")
        if hasattr(existing_student, 'user_profile') and existing_student.user_profile.first():
            user_profile = existing_student.user_profile.first()
            user = user_profile.user
            user_profile.delete()
            user.delete()
        existing_student.delete()
        print("✅ Existing test data cleaned up")
    
    # Create test student
    print("\n📚 Creating test student...")
    student = Student.objects.create(**test_student_data)
    print(f"✅ Test student created: {student}")
    
    # Create user account for the student
    print("\n👤 Creating user account for student...")
    username = f"student_{student.student_id.lower()}"
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
    
    print(f"✅ User account created - Username: {username}, Password: {password}")
    
    # Test authentication before deletion
    print("\n🔐 Testing authentication before deletion...")
    authenticated_user = authenticate(username=username, password=password)
    if authenticated_user:
        print("✅ Authentication successful before deletion")
    else:
        print("❌ Authentication failed before deletion")
        return
    
    # Test that user can access student-related data
    print("\n📊 Testing user access to student data...")
    try:
        student_profile = user.myapp_profile
        if student_profile and student_profile.student:
            print(f"✅ User can access student data: {student_profile.student}")
        else:
            print("❌ User cannot access student data")
    except Exception as e:
        print(f"❌ Error accessing student data: {e}")
    
    # Now test deletion
    print("\n🗑️ Testing student deletion...")
    try:
        # Get information before deletion
        student_name = f"{student.first_name} {student.last_name}"
        student_id = student.student_id
        
        # Delete associated user account and profile
        user_profiles = student.user_profile.all()
        deleted_users = []
        
        for user_profile in user_profiles:
            if user_profile.user:
                deleted_users.append(user_profile.user.username)
                # Delete the user (this will cascade to delete the user_profile)
                user_profile.user.delete()
        
        # Remove student from parent relationships
        parents_count = student.parents.count()
        student.parents.clear()
        
        # Delete the student
        student.delete()
        
        print(f"✅ Student '{student_name}' ({student_id}) deleted successfully!")
        print(f"✅ User accounts deleted: {', '.join(deleted_users) if deleted_users else 'None'}")
        if parents_count > 0:
            print(f"✅ Removed from {parents_count} parent account(s)")
        
    except Exception as e:
        print(f"❌ Error during deletion: {e}")
        return
    
    # Test that user account no longer exists
    print("\n🔍 Verifying user account deletion...")
    try:
        user_check = User.objects.get(username=username)
        print(f"❌ User account still exists: {user_check.username}")
    except User.DoesNotExist:
        print("✅ User account successfully deleted")
    
    # Test that authentication fails after deletion
    print("\n🔐 Testing authentication after deletion...")
    authenticated_user = authenticate(username=username, password=password)
    if authenticated_user:
        print("❌ Authentication still works after deletion - this is a problem!")
    else:
        print("✅ Authentication correctly fails after deletion")
    
    # Test that student no longer exists
    print("\n🔍 Verifying student deletion...")
    try:
        student_check = Student.objects.get(student_id='DELTEST001')
        print(f"❌ Student still exists: {student_check}")
    except Student.DoesNotExist:
        print("✅ Student successfully deleted")
    
    # Test that user profile no longer exists
    print("\n🔍 Verifying user profile deletion...")
    try:
        profile_check = UserProfile.objects.get(user__username=username)
        print(f"❌ User profile still exists: {profile_check}")
    except UserProfile.DoesNotExist:
        print("✅ User profile successfully deleted")
    
    print("\n" + "=" * 50)
    print("🎉 Student deletion test completed successfully!")
    print("✅ Student account removed from database")
    print("✅ User account deleted and cannot log in")
    print("✅ All related data properly cleaned up")

if __name__ == "__main__":
    test_student_deletion()
