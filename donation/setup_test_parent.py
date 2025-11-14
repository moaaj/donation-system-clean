#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from django.contrib.auth.models import User
from myapp.models import Parent, Student, FeeStatus, FeeStructure
from django.utils import timezone
from datetime import timedelta

def setup_test_parent():
    print("=== SETTING UP TEST PARENT ===")
    
    # Get the first parent user
    user = User.objects.filter(username='parent_johnson_1_601').first()
    if not user:
        print("Parent user not found!")
        return
    
    parent = Parent.objects.get(user=user)
    print(f"Parent: {parent.user.get_full_name()} ({user.username})")
    
    # Get first child
    child = parent.students.first()
    print(f"Child: {child.first_name} {child.last_name} ({child.student_id})")
    
    # Create test fee statuses for this child
    fee_structures = FeeStructure.objects.filter(form=child.level_custom)[:3]
    
    created_fees = []
    for fee_structure in fee_structures:
        # Check if fee status already exists
        existing = FeeStatus.objects.filter(
            student=child,
            fee_structure=fee_structure,
            status__in=['pending', 'overdue']
        ).first()
        
        if not existing:
            fee_status = FeeStatus.objects.create(
                student=child,
                fee_structure=fee_structure,
                amount=fee_structure.amount,
                due_date=timezone.now().date() + timedelta(days=30),
                status='pending'
            )
            created_fees.append(fee_status)
            print(f"Created: {fee_status.fee_structure.category.name} - RM {fee_status.amount}")
        else:
            created_fees.append(existing)
            print(f"Existing: {existing.fee_structure.category.name} - RM {existing.amount}")
    
    print(f"\n=== TEST CREDENTIALS ===")
    print(f"Username: {user.username}")
    print(f"Password: parent123")
    print(f"Child: {child.first_name} {child.last_name}")
    print(f"Available fees: {len(created_fees)}")
    print(f"Total amount: RM {sum(f.amount for f in created_fees)}")
    
    print(f"\n=== TEST INSTRUCTIONS ===")
    print(f"1. Login with: {user.username} / parent123")
    print(f"2. Go to: http://127.0.0.1:8000/school-fees/")
    print(f"3. Should auto-redirect to parent dashboard")
    print(f"4. Click 'View & Pay Fees' for {child.first_name}")
    print(f"5. Add fees to cart and test checkout")

if __name__ == '__main__':
    setup_test_parent()
