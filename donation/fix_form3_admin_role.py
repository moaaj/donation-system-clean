#!/usr/bin/env python
"""
Fix Form 3 admin role
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

def fix_form3_admin_role():
    """Fix Form 3 admin role"""
    
    print("🔧 FIXING FORM 3 ADMIN ROLE")
    print("=" * 70)
    
    try:
        # Get the Form 3 admin user
        form3_admin = User.objects.get(username='form3_admin')
        profile = form3_admin.profile
        
        print(f"📝 Current role: {profile.role}")
        
        # Update the role to form3_admin
        profile.role = 'form3_admin'
        profile.save()
        
        print(f"✅ Updated role to: {profile.role}")
        print(f"✅ Is Form 3 admin: {profile.is_form3_admin()}")
        
        return True
        
    except User.DoesNotExist:
        print("❌ Form 3 admin user does not exist!")
        return False
    except Exception as e:
        print(f"❌ Error fixing Form 3 admin role: {str(e)}")
        return False

if __name__ == "__main__":
    fix_form3_admin_role()
