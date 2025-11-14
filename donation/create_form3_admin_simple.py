#!/usr/bin/env python
"""
Simple script to create Form 3 admin user
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

def create_form3_admin_simple():
    """Create a Form 3 admin user for testing"""
    
    print("👨‍💼 CREATING FORM 3 ADMIN USER (SIMPLE)")
    print("=" * 70)
    
    # Check if user already exists
    if User.objects.filter(username='form3_admin').exists():
        print("✅ Form 3 admin already exists!")
        user = User.objects.get(username='form3_admin')
        print(f"   👤 Username: {user.username}")
        print(f"   🔑 Password: form3admin123")
        return user
    
    # Create user account
    user = User.objects.create_user(
        username='form3_admin',
        email='form3_admin@school.com',
        password='form3admin123',
        first_name='Form 3',
        last_name='Administrator',
        is_staff=True,
        is_superuser=False
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
    print(f"   🎭 Role: {user_profile.get_role_display()}")
    
    return user

if __name__ == "__main__":
    create_form3_admin_simple()
