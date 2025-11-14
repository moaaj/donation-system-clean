#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from django.contrib.auth.models import User
from myapp.models import UserProfile, Parent

def fix_moaaj_user():
    print("=== FIXING MOAAJ USER ===")
    
    try:
        moaaj = User.objects.get(username='moaaj')
        print(f"Found moaaj user: {moaaj.username}")
        print(f"Is superuser: {moaaj.is_superuser}")
        
        # Fix UserProfile role
        try:
            profile = moaaj.myapp_profile
            print(f"Current UserProfile role: {profile.role}")
            
            if profile.role == 'parent':
                profile.role = 'admin'
                profile.save()
                print(f"✅ Updated moaaj role to: {profile.role}")
            else:
                print(f"✅ moaaj role is already: {profile.role}")
                
        except UserProfile.DoesNotExist:
            print("No UserProfile found for moaaj")
        
        # Remove Parent record if it exists
        try:
            parent = Parent.objects.get(user=moaaj)
            parent.delete()
            print("✅ Removed Parent record for moaaj")
        except Parent.DoesNotExist:
            print("✅ No Parent record to remove for moaaj")
            
        print(f"\n=== VERIFICATION ===")
        try:
            profile = moaaj.myapp_profile
            print(f"moaaj UserProfile role: {profile.role}")
        except:
            print("moaaj has no UserProfile")
            
        try:
            parent = Parent.objects.get(user=moaaj)
            print(f"moaaj has Parent record: Yes")
        except Parent.DoesNotExist:
            print("moaaj has no Parent record: ✅")
            
        print(f"\nmoaaj is now properly configured as admin/superuser!")
        
    except User.DoesNotExist:
        print("moaaj user not found!")

if __name__ == '__main__':
    fix_moaaj_user()
