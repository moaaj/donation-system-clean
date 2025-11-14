#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from django.contrib.auth.models import User
from myapp.models import Parent

def main():
    parents = Parent.objects.all().select_related('user')
    
    print("=== ALL PARENT LOGIN CREDENTIALS ===")
    print(f"Total Parents: {parents.count()}")
    print()
    
    for i, parent in enumerate(parents, 1):
        print(f"{i:2d}. Username: {parent.user.username}")
        print(f"    Password: parent123")
        print(f"    Name: {parent.user.get_full_name()}")
        print(f"    Email: {parent.user.email}")
        print(f"    Children: {parent.students.count()}")
        print(f"    Phone: {parent.phone_number}")
        print()
    
    print("=== LOGIN INSTRUCTIONS ===")
    print("1. Go to: http://127.0.0.1:8000/accounts/login/")
    print("2. Use any username above with password: parent123")
    print("3. After login, go to: http://127.0.0.1:8000/parent/")
    print("4. Or access parent portal directly after login")
    print()
    print("=== QUICK ACCESS SAMPLE CREDENTIALS ===")
    print("Username: parent_abdullah_1_125 | Password: parent123")
    print("Username: parent_johnson_1_869 | Password: parent123")
    print("Username: parent_hassan_1_791 | Password: parent123")

if __name__ == '__main__':
    main()
