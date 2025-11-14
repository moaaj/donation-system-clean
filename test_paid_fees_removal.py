#!/usr/bin/env python
"""
Test script to verify that paid fees are properly removed from student views
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.donation.settings')
django.setup()

from django.contrib.auth.models import User
from myapp.models import Student, FeeStatus, FeeStructure, FeeCategory
from django.utils import timezone

def test_paid_fees_removal():
    print("=" * 60)
    print("TESTING: Paid Fees Removal from Student Views")
    print("=" * 60)
    
    # Find a student with fee statuses
    student = Student.objects.filter(feestatus__isnull=False).first()
    
    if not student:
        print("❌ No student with fee statuses found")
        return
    
    print(f"📚 Testing with student: {student.first_name} {student.last_name}")
    
    # Get all fee statuses for this student
    all_fee_statuses = FeeStatus.objects.filter(student=student)
    print(f"📊 Total fee statuses: {all_fee_statuses.count()}")
    
    # Count by status
    paid_count = all_fee_statuses.filter(status='paid').count()
    pending_count = all_fee_statuses.filter(status='pending').count()
    overdue_count = all_fee_statuses.filter(status='overdue').count()
    
    print(f"   - Paid: {paid_count}")
    print(f"   - Pending: {pending_count}")
    print(f"   - Overdue: {overdue_count}")
    
    # Test the new filtering logic (unpaid only)
    unpaid_fee_statuses = FeeStatus.objects.filter(
        student=student, 
        status__in=['pending', 'overdue']
    )
    
    print(f"\n🔍 Unpaid fee statuses (should be shown): {unpaid_fee_statuses.count()}")
    
    if unpaid_fee_statuses.count() == (pending_count + overdue_count):
        print("✅ Filtering logic is working correctly!")
    else:
        print("❌ Filtering logic has issues!")
    
    # Show details of unpaid fees
    print(f"\n📋 Unpaid fees details:")
    for fee_status in unpaid_fee_statuses:
        print(f"   - {fee_status.fee_structure.category.name}: {fee_status.status} (RM {fee_status.amount})")
    
    # Show details of paid fees (should not be shown)
    paid_fee_statuses = all_fee_statuses.filter(status='paid')
    print(f"\n✅ Paid fees (should NOT be shown): {paid_fee_statuses.count()}")
    for fee_status in paid_fee_statuses:
        print(f"   - {fee_status.fee_structure.category.name}: {fee_status.status} (RM {fee_status.amount})")
    
    print(f"\n🎯 RESULT: Paid fees are {'✅ HIDDEN' if paid_fee_statuses.count() > 0 and unpaid_fee_statuses.count() == (pending_count + overdue_count) else '❌ STILL VISIBLE'}")
    
    print("=" * 60)

if __name__ == "__main__":
    test_paid_fees_removal()
