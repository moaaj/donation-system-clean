#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from django.contrib.auth.models import User
from myapp.models import Parent, Student, FeeStatus

def test_parent_data():
    print("=== TESTING PARENT CHECKOUT DATA ===")
    
    # Get a parent user
    parent_user = User.objects.filter(username__startswith='parent_').first()
    if not parent_user:
        print("No parent users found!")
        return
    
    parent = Parent.objects.get(user=parent_user)
    print(f"Parent: {parent.user.get_full_name()} ({parent_user.username})")
    
    # Get first child
    child = parent.students.first()
    if not child:
        print("Parent has no children!")
        return
    
    print(f"Child: {child.first_name} {child.last_name} ({child.student_id})")
    
    # Get outstanding fees
    fee_statuses = FeeStatus.objects.filter(
        student=child, 
        status__in=['pending', 'overdue']
    )[:3]
    
    print(f"Outstanding fees for {child.first_name}: {fee_statuses.count()}")
    for fs in fee_statuses:
        print(f"  - {fs.fee_structure.category.name}: RM {fs.amount} ({fs.status})")
    
    print(f"\nLogin credentials:")
    print(f"Username: {parent_user.username}")
    print(f"Password: parent123")
    print(f"\nCheckout test ready!")

if __name__ == '__main__':
    test_parent_data()
