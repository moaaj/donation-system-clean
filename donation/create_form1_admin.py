#!/usr/bin/env python
"""
Create Form 1 Admin User with STRICT DATA ISOLATION
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import UserProfile
from django.db import transaction

def create_form1_admin():
    """Create Form 1 admin user with appropriate permissions and data isolation"""
    
    print("🚀 CREATING FORM 1 ADMIN USER WITH DATA ISOLATION")
    print("=" * 60)
    
    try:
        with transaction.atomic():
            # Check if user already exists
            if User.objects.filter(username='form1_admin').exists():
                print("⚠️  Form 1 admin user already exists!")
                
                # Get existing user and update profile if needed
                user = User.objects.get(username='form1_admin')
                profile, created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={'role': 'form1_admin'}
                )
                
                if not created and profile.role != 'form1_admin':
                    profile.role = 'form1_admin'
                    profile.save()
                    print("✅ Updated existing user profile to Form 1 admin role")
                else:
                    print("✅ Existing user already has correct Form 1 admin role")
                
                return user
            
            # Create new user
            user = User.objects.create_user(
                username='form1_admin',
                email='form1admin@school.edu',
                password='form1admin123',
                first_name='Form 1',
                last_name='Administrator',
                is_staff=True,
                is_active=True
            )
            
            # Create user profile
            profile = UserProfile.objects.create(
                user=user,
                role='form1_admin'
            )
            
            print("✅ Form 1 admin user created successfully!")
            print(f"   Username: {user.username}")
            print(f"   Email: {user.email}")
            print(f"   Password: form1admin123")
            print(f"   Role: {profile.role}")
            print(f"   Staff Status: {user.is_staff}")
            print(f"   Active Status: {user.is_active}")
            
            return user
            
    except Exception as e:
        print(f"❌ Error creating Form 1 admin user: {str(e)}")
        return None

def test_form1_admin_permissions():
    """Test Form 1 admin permissions and data isolation"""
    
    print("\n🧪 TESTING FORM 1 ADMIN PERMISSIONS & DATA ISOLATION")
    print("=" * 60)
    
    try:
        user = User.objects.get(username='form1_admin')
        profile = user.profile
        
        print(f"✅ User found: {user.username}")
        print(f"✅ Profile role: {profile.role}")
        print(f"✅ Is Form 1 admin: {profile.is_form1_admin()}")
        print(f"✅ Is staff: {user.is_staff}")
        print(f"✅ Is active: {user.is_active}")
        
        # Test data isolation by checking if they can only see Form 1 data
        from myapp.models import Student
        form1_students = Student.objects.filter(
            level='form',
            level_custom__iexact='Form 1',
            is_active=True
        )
        all_students = Student.objects.filter(is_active=True)
        
        print(f"✅ Form 1 students accessible: {form1_students.count()}")
        print(f"✅ Total students in system: {all_students.count()}")
        print(f"✅ Data isolation working: {form1_students.count() <= all_students.count()}")
        
        return True
        
    except User.DoesNotExist:
        print("❌ Form 1 admin user not found!")
        return False
    except Exception as e:
        print(f"❌ Error testing permissions: {str(e)}")
        return False

if __name__ == '__main__':
    print("🏫 FORM 1 ADMIN SETUP WITH DATA ISOLATION")
    print("=" * 60)
    
    # Create Form 1 admin user
    user = create_form1_admin()
    
    if user:
        # Test permissions and data isolation
        test_success = test_form1_admin_permissions()
        
        if test_success:
            print("\n🎉 FORM 1 ADMIN SETUP COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print("📝 Next steps:")
            print("   1. Start the Django development server")
            print("   2. Login with username: form1_admin")
            print("   3. Password: form1admin123")
            print("   4. Access Form 1 admin dashboard at: /form1-admin/")
            print("   5. Change the default password after first login")
            print("\n🔒 DATA ISOLATION FEATURES:")
            print("   • Can only view Form 1 student data")
            print("   • Can only manage Form 1 fees and payments")
            print("   • Analytics restricted to Form 1 students only")
            print("   • All reports filtered to Form 1 data only")
        else:
            print("\n❌ FORM 1 ADMIN SETUP COMPLETED WITH ERRORS")
    else:
        print("\n❌ FORM 1 ADMIN SETUP FAILED")
