#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from django.contrib.auth.models import User
from myapp.models import UserProfile, Parent

def check_moaaj_user():
    print("=== CHECKING MOAAJ USER ===")
    
    try:
        moaaj = User.objects.get(username='moaaj')
        print(f"moaaj user: {moaaj.username}")
        print(f"Is superuser: {moaaj.is_superuser}")
        print(f"Is staff: {moaaj.is_staff}")
        
        try:
            profile = moaaj.myapp_profile
            print(f"UserProfile role: {profile.role}")
        except UserProfile.DoesNotExist:
            print("No UserProfile found")
        
        try:
            parent = Parent.objects.get(user=moaaj)
            print(f"Has Parent record: Yes")
        except Parent.DoesNotExist:
            print("No Parent record")
            
    except User.DoesNotExist:
        print("moaaj user not found!")

if __name__ == '__main__':
    check_moaaj_user()
