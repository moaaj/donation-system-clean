#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from myapp.models import UserProfile, Parent
from django.contrib.auth.models import User

def check_and_fix_parent_profiles():
    print("=== CHECKING PARENT USER PROFILES ===")
    
    parent_users = User.objects.filter(username__startswith='parent_')
    print(f"Total parent users: {parent_users.count()}")
    
    profiles = UserProfile.objects.filter(user__in=parent_users)
    print(f"Parent profiles found: {profiles.count()}")
    
    print("\nExisting profiles:")
    for p in profiles:
        print(f"  {p.user.username}: {p.role}")
    
    print("\nChecking for missing profiles:")
    missing_count = 0
    for user in parent_users:
        try:
            profile = user.myapp_profile
            print(f"  ✅ {user.username}: {profile.role}")
        except UserProfile.DoesNotExist:
            print(f"  ❌ MISSING: {user.username}")
            missing_count += 1
    
    if missing_count > 0:
        print(f"\n=== FIXING {missing_count} MISSING PROFILES ===")
        for user in parent_users:
            try:
                profile = user.myapp_profile
            except UserProfile.DoesNotExist:
                # Get parent info
                try:
                    parent = Parent.objects.get(user=user)
                    profile = UserProfile.objects.create(
                        user=user,
                        role='parent',
                        phone_number=parent.phone_number,
                        address=parent.address
                    )
                    print(f"  ✅ Created profile for {user.username}")
                except Parent.DoesNotExist:
                    print(f"  ❌ No Parent record for {user.username}")
        
        print("\n=== VERIFICATION ===")
        for user in parent_users:
            try:
                profile = user.myapp_profile
                print(f"  ✅ {user.username}: {profile.role}")
            except UserProfile.DoesNotExist:
                print(f"  ❌ STILL MISSING: {user.username}")
    
    print(f"\nAll parent users should now have UserProfile records!")

if __name__ == '__main__':
    check_and_fix_parent_profiles()
