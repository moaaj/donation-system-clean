#!/usr/bin/env python
"""
Create some overdue payments for testing the payment reminders dashboard
"""

import os
import sys
import django
from decimal import Decimal

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from myapp.models import Student, UserProfile, FeeCategory, FeeStructure, FeeStatus, IndividualStudentFee, FeeWaiver, Payment
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta

def create_overdue_payments():
    """Create some overdue payments for testing"""
    
    print("📅 Creating Overdue Payments for Testing")
    print("=" * 70)
    
    # Get all pending fee status records
    pending_fees = FeeStatus.objects.filter(
        status='pending'
    ).select_related('student', 'fee_structure__category')
    
    print(f"📊 Found {pending_fees.count()} pending fee status records")
    
    # Make some payments overdue (set due date to past dates)
    overdue_count = 0
    
    for i, fee in enumerate(pending_fees):
        if i < 2:  # Make first 2 payments overdue
            # Set due date to 5 days ago
            fee.due_date = date.today() - timedelta(days=5)
            fee.save()
            overdue_count += 1
            
            print(f"✅ Made overdue: {fee.student.first_name} {fee.student.last_name}")
            print(f"   Fee: {fee.fee_structure.category.name}")
            print(f"   Amount: RM {fee.amount}")
            print(f"   Due Date: {fee.due_date} (5 days ago)")
            print()
    
    print(f"🎉 Created {overdue_count} overdue payments")
    
    # Verify the changes
    print("\n" + "=" * 70)
    print("📋 VERIFICATION")
    print("=" * 70)
    
    today = date.today()
    overdue_payments = FeeStatus.objects.filter(
        status='pending',
        due_date__lt=today
    ).select_related('student', 'fee_structure__category')
    
    upcoming_payments = FeeStatus.objects.filter(
        status='pending',
        due_date__gte=today
    ).select_related('student', 'fee_structure__category')
    
    print(f"📊 Overdue payments: {overdue_payments.count()}")
    print(f"📊 Upcoming payments: {upcoming_payments.count()}")
    
    # Calculate totals
    total_overdue = 0
    total_upcoming = 0
    
    for fee in overdue_payments:
        try:
            discounted_amount = fee.get_discounted_amount()
            total_overdue += float(discounted_amount)
        except:
            total_overdue += float(fee.amount)
    
    for fee in upcoming_payments:
        try:
            discounted_amount = fee.get_discounted_amount()
            total_upcoming += float(discounted_amount)
        except:
            total_upcoming += float(fee.amount)
    
    print(f"💰 Total Overdue Amount: RM {total_overdue:.2f}")
    print(f"💰 Total Upcoming Amount: RM {total_upcoming:.2f}")
    
    print("\n" + "=" * 70)
    print("🎯 PAYMENT REMINDERS DASHBOARD STATUS")
    print("=" * 70)
    
    if total_overdue > 0:
        print("✅ Overdue payments will be displayed in the dashboard")
        print("   - Red section will show overdue payments")
        print("   - Days overdue will be calculated correctly")
    else:
        print("ℹ️  No overdue payments to display")
    
    if total_upcoming > 0:
        print("✅ Upcoming payments will be displayed in the dashboard")
        print("   - Yellow section will show upcoming payments")
        print("   - Days until due will be calculated correctly")
    else:
        print("ℹ️  No upcoming payments to display")
    
    print("\n" + "=" * 70)
    print("🚀 NEXT STEPS")
    print("=" * 70)
    
    print("1. Access the Payment Reminders dashboard in the web interface")
    print("2. Verify that both overdue and upcoming sections are populated")
    print("3. Check that overdue payments show correct days overdue")
    print("4. Check that upcoming payments show correct days until due")
    print("5. Test the 'Send Reminder' functionality for both sections")
    print("6. Verify that discounted amounts are shown correctly")

if __name__ == "__main__":
    create_overdue_payments()

