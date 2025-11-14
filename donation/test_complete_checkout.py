#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from django.contrib.auth.models import User
from myapp.models import Parent, Student, FeeStatus, FeeStructure, Payment
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore

def test_complete_checkout():
    print("=== TESTING COMPLETE CHECKOUT PROCESS ===")
    
    # Get Michael Johnson user
    user = User.objects.get(username='parent_johnson_1_869')
    parent = Parent.objects.get(user=user)
    child = parent.students.first()
    
    print(f"Parent: {parent.user.get_full_name()}")
    print(f"Child: {child.first_name} {child.last_name}")
    
    # Clear any existing cart
    print("\n=== CLEARING EXISTING CART ===")
    sessions = Session.objects.all()
    for session in sessions:
        session_data = session.get_decoded()
        if '_auth_user_id' in session_data and str(session_data['_auth_user_id']) == str(user.id):
            session_store = SessionStore(session_key=session.session_key)
            session_store['parent_cart'] = {'fees': [], 'fee_statuses': [], 'individual_fees': []}
            session_store.save()
            print("✅ Cleared existing cart")
            break
    
    # Get outstanding fees
    outstanding_fees = FeeStatus.objects.filter(
        student=child,
        status__in=['pending', 'overdue']
    )
    
    print(f"\n=== AVAILABLE FEES FOR TESTING ===")
    print(f"Outstanding fees: {outstanding_fees.count()}")
    for fee in outstanding_fees:
        print(f"  ID {fee.id}: {fee.fee_structure.category.name} - RM {fee.amount} ({fee.status})")
    
    if outstanding_fees.count() > 0:
        # Simulate adding fees to cart
        print(f"\n=== SIMULATING CART OPERATIONS ===")
        test_fee = outstanding_fees.first()
        print(f"Simulating adding fee status ID {test_fee.id} to cart")
        
        # Find user session and add to cart
        for session in sessions:
            session_data = session.get_decoded()
            if '_auth_user_id' in session_data and str(session_data['_auth_user_id']) == str(user.id):
                session_store = SessionStore(session_key=session.session_key)
                current_cart = session_store.get('parent_cart', {'fees': [], 'fee_statuses': [], 'individual_fees': []})
                current_cart['fee_statuses'].append(str(test_fee.id))
                session_store['parent_cart'] = current_cart
                session_store.save()
                print(f"✅ Added fee to cart: {current_cart}")
                break
        
        print(f"\n=== CHECKOUT TEST INSTRUCTIONS ===")
        print(f"1. Login with: {user.username} / parent123")
        print(f"2. Go to /school-fees/ (should redirect to parent dashboard)")
        print(f"3. Cart should show 1 item")
        print(f"4. Click 'View Cart' to see the fee")
        print(f"5. Click 'Proceed to Checkout'")
        print(f"6. Click 'Complete Payment'")
        print(f"7. Verify receipt appears and cart becomes empty")
        print(f"8. Go back to dashboard - cart should show 'Empty'")
    
    else:
        print("No outstanding fees available for testing!")

if __name__ == '__main__':
    test_complete_checkout()
