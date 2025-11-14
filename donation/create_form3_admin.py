#!/usr/bin/env python
"""
Create Form 3 admin user for testing Form 3 admin functionality
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from accounts.models import UserProfile
from django.contrib.auth.models import User

def create_form3_admin():
    """Create a Form 3 admin user for testing"""
    
    print("👨‍💼 CREATING FORM 3 ADMIN USER")
    print("=" * 70)
    
    # Clean up existing Form 3 admin if exists
    existing_admin = User.objects.filter(username='form3_admin').first()
    if existing_admin:
        print("🧹 Cleaning up existing Form 3 admin...")
        # Delete user profile first
        try:
            existing_admin.profile.delete()
        except:
            pass
        existing_admin.delete()
        print("✅ Existing Form 3 admin removed")
    
    # Create Form 3 admin user
    print("\n📝 Creating Form 3 admin user...")
    
    try:
        # Create user account
        user = User.objects.create_user(
            username='form3_admin',
            email='form3_admin@school.com',
            password='form3admin123',
            first_name='Form 3',
            last_name='Administrator',
            is_staff=True,  # Give staff privileges for admin access
            is_superuser=False  # Not a superuser, just Form 3 admin
        )
        
        # Create user profile with Form 3 admin role
        user_profile = UserProfile.objects.create(
            user=user,
            role='form3_admin',
            phone_number='+60123456789',
            address='School Administration Office',
            is_verified=True
        )
        
        print("✅ Form 3 admin user created successfully!")
        print(f"   👤 Username: form3_admin")
        print(f"   🔑 Password: form3admin123")
        print(f"   📧 Email: form3_admin@school.com")
        print(f"   🎭 Role: {user_profile.get_role_display()}")
        print(f"   📱 Phone: {user_profile.phone_number}")
        
        print(f"\n🎯 FORM 3 ADMIN CREATION COMPLETED!")
        print("=" * 70)
        print("✅ Form 3 admin user account created")
        print("✅ User profile with form3_admin role assigned")
        print("✅ Staff privileges granted for admin access")
        
        print(f"\n🚀 NEXT STEPS:")
        print("=" * 70)
        print("1. Login as form3_admin to test Form 3 admin functionality")
        print("2. Verify Form 3 admin can access Form 3 student management")
        print("3. Test Form 3 admin can view and manage Form 3 students only")
        print("4. Test Form 3 admin can manage Form 3 fees and payments")
        
        return user
        
    except Exception as e:
        print(f"❌ Error creating Form 3 admin: {str(e)}")
        return None

if __name__ == "__main__":
    create_form3_admin()
