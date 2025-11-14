#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from django.contrib.auth.models import User
from myapp.models import Parent, Student, FeeStatus, FeeStructure, Payment
from django.utils import timezone
from datetime import timedelta

def setup_test_data():
    print("=== SETTING UP TEST DATA ===")
    
    # Get a parent user
    parent_user = User.objects.filter(username__startswith='parent_').first()
    parent = Parent.objects.get(user=parent_user)
    print(f"Parent: {parent.user.get_full_name()} ({parent_user.username})")
    
    # Get first child
    child = parent.students.first()
    print(f"Child: {child.first_name} {child.last_name} ({child.student_id})")
    
    # Create multiple test fee statuses for this child
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
    
    print(f"\nTotal test fees available: {len(created_fees)}")
    print(f"Total amount: RM {sum(f.amount for f in created_fees)}")
    
    return parent_user.username, child.id, [f.id for f in created_fees]

def test_checkout_simulation():
    print("\n=== SIMULATING CHECKOUT PROCESS ===")
    
    username, child_id, fee_status_ids = setup_test_data()
    
    print(f"\nTest Instructions:")
    print(f"1. Login with: {username} / parent123")
    print(f"2. Go to /school-fees/ (auto-redirects to parent dashboard)")
    print(f"3. Click 'View & Pay Fees' for the child")
    print(f"4. Add fees to cart using 'Add to Cart' buttons")
    print(f"5. Click 'View Cart' to review")
    print(f"6. Click 'Proceed to Checkout'")
    print(f"7. Select payment method and click 'Complete Payment'")
    print(f"8. Verify: Receipt appears with invoice links")
    print(f"9. Check: Cart should be empty")
    
    # Test cart simulation
    print(f"\n=== SIMULATING CART OPERATIONS ===")
    print(f"Simulating adding fee status IDs to cart: {fee_status_ids}")
    
    # Simulate session cart
    test_cart = {
        'fees': [],
        'fee_statuses': [str(fid) for fid in fee_status_ids],
        'individual_fees': []
    }
    
    print(f"Simulated cart: {test_cart}")
    print(f"Cart items count: {len(test_cart['fee_statuses'])}")
    
    # Calculate expected total
    fee_statuses = FeeStatus.objects.filter(id__in=fee_status_ids)
    expected_total = sum(fs.get_discounted_amount() for fs in fee_statuses)
    print(f"Expected checkout total: RM {expected_total}")
    
    print(f"\nCheckout test ready!")

if __name__ == '__main__':
    test_checkout_simulation()
