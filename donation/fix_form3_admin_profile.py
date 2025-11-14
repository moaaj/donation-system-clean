#!/usr/bin/env python
"""
Fix Form 3 admin profile to ensure proper access
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

def fix_form3_admin_profile():
    """Fix Form 3 admin profile to ensure proper access"""
    
    print("🔧 FIXING FORM 3 ADMIN PROFILE")
    print("=" * 70)
    
    try:
        # Get the Form 3 admin user
        form3_admin = User.objects.get(username='form3_admin')
        
        print(f"📝 User found: {form3_admin.username}")
        print(f"📝 Is staff: {form3_admin.is_staff}")
        print(f"📝 Is superuser: {form3_admin.is_superuser}")
        
        # Check if profile exists
        try:
            profile = form3_admin.profile
            print(f"📝 Profile exists: {profile.role}")
            print(f"📝 Is Form 3 admin: {profile.is_form3_admin()}")
        except:
            print("❌ Profile does not exist, creating...")
            profile = UserProfile.objects.create(
                user=form3_admin,
                role='form3_admin',
                phone_number='+60123456789',
                address='School Administration Office',
                is_verified=True
            )
            print("✅ Profile created")
        
        # Ensure user has staff privileges
        if not form3_admin.is_staff:
            form3_admin.is_staff = True
            form3_admin.save()
            print("✅ Staff privileges granted")
        
        # Ensure profile has correct role
        if profile.role != 'form3_admin':
            profile.role = 'form3_admin'
            profile.save()
            print("✅ Role updated to form3_admin")
        
        print(f"\n🎯 FINAL STATUS:")
        print(f"✅ Username: {form3_admin.username}")
        print(f"✅ Is staff: {form3_admin.is_staff}")
        print(f"✅ Is superuser: {form3_admin.is_superuser}")
        print(f"✅ Profile role: {profile.role}")
        print(f"✅ Is Form 3 admin: {profile.is_form3_admin()}")
        
        return True
        
    except User.DoesNotExist:
        print("❌ Form 3 admin user does not exist!")
        return False
    except Exception as e:
        print(f"❌ Error fixing Form 3 admin profile: {str(e)}")
        return False

if __name__ == "__main__":
    fix_form3_admin_profile()
