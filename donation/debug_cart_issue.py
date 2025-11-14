#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from django.contrib.auth.models import User
from myapp.models import Parent, FeeStatus, Payment
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore

def debug_cart_issue():
    print("=== DEBUGGING CART ISSUE ===")
    
    # Get Michael Johnson user
    try:
        user = User.objects.get(username='parent_johnson_1_869')
        parent = Parent.objects.get(user=user)
        print(f"Parent: {parent.user.get_full_name()}")
        
        # Check recent payments
        recent_payments = Payment.objects.filter(
            student__in=parent.students.all()
        ).order_by('-created_at')[:5]
        
        print(f"\nRecent payments:")
        for payment in recent_payments:
            print(f"  {payment.payment_date} - {payment.student.first_name} - {payment.fee_structure.category.name if payment.fee_structure else 'Individual'} - RM {payment.amount}")
        
        # Check outstanding fees for first child
        child = parent.students.first()
        outstanding_fees = FeeStatus.objects.filter(
            student=child,
            status__in=['pending', 'overdue']
        )
        
        print(f"\nOutstanding fees for {child.first_name}:")
        for fee in outstanding_fees:
            print(f"  {fee.fee_structure.category.name} - RM {fee.amount} - {fee.status}")
        
        # Check if there are any active sessions for this user
        print(f"\nChecking for active sessions...")
        sessions = Session.objects.all()
        for session in sessions:
            session_data = session.get_decoded()
            if '_auth_user_id' in session_data and str(session_data['_auth_user_id']) == str(user.id):
                print(f"Found session for user {user.username}")
                parent_cart = session_data.get('parent_cart', {})
                print(f"Parent cart in session: {parent_cart}")
                
                if parent_cart and any(parent_cart.values()):
                    print("⚠️  Cart is not empty in session!")
                    # Clear the cart
                    session_store = SessionStore(session_key=session.session_key)
                    session_store['parent_cart'] = {'fees': [], 'fee_statuses': [], 'individual_fees': []}
                    session_store.save()
                    print("✅ Cleared cart in session")
                else:
                    print("✅ Cart is empty in session")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    debug_cart_issue()
