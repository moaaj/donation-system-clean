#!/usr/bin/env python
"""
Test Payment Reminders functionality
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

def test_payment_reminders():
    """Test Payment Reminders functionality"""
    
    print("🧪 Testing Payment Reminders Functionality")
    print("=" * 70)
    
    # Get all pending fee status records
    pending_fees = FeeStatus.objects.filter(
        status='pending'
    ).select_related('student', 'fee_structure__category').order_by('due_date')
    
    print(f"📊 Total pending fee status records: {pending_fees.count()}")
    
    # Separate overdue and upcoming payments
    today = timezone.now().date()
    overdue_payments = pending_fees.filter(due_date__lt=today)
    upcoming_payments = pending_fees.filter(due_date__gte=today)
    
    print(f"📊 Overdue payments: {overdue_payments.count()}")
    print(f"📊 Upcoming payments: {upcoming_payments.count()}")
    
    # Calculate totals using the discounted amounts
    total_overdue = 0
    total_upcoming = 0
    
    print("\n" + "=" * 70)
    print("📋 OVERDUE PAYMENTS")
    print("=" * 70)
    
    if overdue_payments.count() == 0:
        print("✅ No overdue payments found")
    else:
        for fee in overdue_payments:
            try:
                discounted_amount = fee.get_discounted_amount()
                total_overdue += float(discounted_amount)
                
                days_overdue = (today - fee.due_date).days
                
                print(f"👤 {fee.student.first_name} {fee.student.last_name}")
                print(f"   📚 Form: {fee.student.get_level_display_value()}")
                print(f"   💰 Fee Category: {fee.fee_structure.category.name}")
                print(f"   💵 Original Amount: RM {fee.amount}")
                print(f"   💵 Discounted Amount: RM {discounted_amount}")
                print(f"   📅 Due Date: {fee.due_date}")
                print(f"   ⏰ Days Overdue: {days_overdue}")
                
                # Check if discounts are applied
                try:
                    discount_info = fee.get_discount_info()
                    if discount_info['has_discount']:
                        print(f"   🎯 Discount Applied: RM {discount_info['total_discount']}")
                        for waiver_info in discount_info['waivers']:
                            print(f"      • {waiver_info['type']}: {waiver_info['percentage']}%")
                except Exception as e:
                    print(f"   ⚠️  Error getting discount info: {str(e)}")
                
                print()
                
            except Exception as e:
                print(f"   ⚠️  Error processing fee: {str(e)}")
                total_overdue += float(fee.amount)
    
    print("\n" + "=" * 70)
    print("📋 UPCOMING PAYMENTS")
    print("=" * 70)
    
    if upcoming_payments.count() == 0:
        print("✅ No upcoming payments found")
    else:
        for fee in upcoming_payments:
            try:
                discounted_amount = fee.get_discounted_amount()
                total_upcoming += float(discounted_amount)
                
                days_until = (fee.due_date - today).days
                
                print(f"👤 {fee.student.first_name} {fee.student.last_name}")
                print(f"   📚 Form: {fee.student.get_level_display_value()}")
                print(f"   💰 Fee Category: {fee.fee_structure.category.name}")
                print(f"   💵 Original Amount: RM {fee.amount}")
                print(f"   💵 Discounted Amount: RM {discounted_amount}")
                print(f"   📅 Due Date: {fee.due_date}")
                print(f"   ⏰ Days Until Due: {days_until}")
                
                # Check if discounts are applied
                try:
                    discount_info = fee.get_discount_info()
                    if discount_info['has_discount']:
                        print(f"   🎯 Discount Applied: RM {discount_info['total_discount']}")
                        for waiver_info in discount_info['waivers']:
                            print(f"      • {waiver_info['type']}: {waiver_info['percentage']}%")
                except Exception as e:
                    print(f"   ⚠️  Error getting discount info: {str(e)}")
                
                print()
                
            except Exception as e:
                print(f"   ⚠️  Error processing fee: {str(e)}")
                total_upcoming += float(fee.amount)
    
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    
    print(f"💰 Total Overdue Amount: RM {total_overdue:.2f}")
    print(f"💰 Total Upcoming Amount: RM {total_upcoming:.2f}")
    print(f"📊 Total Pending Fees: {pending_fees.count()}")
    
    print("\n" + "=" * 70)
    print("🎯 PAYMENT REMINDERS DASHBOARD STATUS")
    print("=" * 70)
    
    if total_overdue > 0:
        print("✅ Overdue payments will be displayed in the dashboard")
    else:
        print("ℹ️  No overdue payments to display")
    
    if total_upcoming > 0:
        print("✅ Upcoming payments will be displayed in the dashboard")
    else:
        print("ℹ️  No upcoming payments to display")
    
    print("\n" + "=" * 70)
    print("🚀 NEXT STEPS")
    print("=" * 70)
    
    print("1. Access the Payment Reminders dashboard in the web interface")
    print("2. Verify that overdue and upcoming payments are displayed correctly")
    print("3. Test the 'Send Reminder' functionality")
    print("4. Test the 'Generate Letter' functionality")
    print("5. Verify that discounted amounts are shown correctly")

if __name__ == "__main__":
    test_payment_reminders()

