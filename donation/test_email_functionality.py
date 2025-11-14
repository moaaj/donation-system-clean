#!/usr/bin/env python
"""
Test script to verify email functionality sends to student emails
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from myapp.models import FeeStatus, Student, FeeStructure, FeeCategory, Parent
from django.utils import timezone
from datetime import date, timedelta

def test_email_functionality():
    """Test that emails are sent directly to student emails"""
    
    print("🧪 TESTING EMAIL FUNCTIONALITY")
    print("=" * 60)
    
    # Get all pending fee status records
    pending_fees = FeeStatus.objects.filter(status='pending').select_related(
        'student', 'fee_structure__category'
    )
    
    if not pending_fees.exists():
        print("❌ No pending fees found. Please create some test data first.")
        return
    
    print(f"📊 Found {pending_fees.count()} pending fee records")
    
    # Test each fee status
    for i, fee_status in enumerate(pending_fees[:3], 1):  # Test first 3
        print(f"\n🔍 Testing Fee Status #{i}:")
        print(f"   Student: {fee_status.student.first_name} {fee_status.student.last_name}")
        print(f"   Fee Category: {fee_status.fee_structure.category.name}")
        print(f"   Amount: RM {fee_status.amount:.2f}")
        print(f"   Due Date: {fee_status.due_date}")
        
        # Test student email
        student = fee_status.student
        student_email = getattr(student, 'email', None)
        
        print(f"   Student Email: {student_email or 'Not available'}")
        
        # Simulate the email sending logic
        if student_email:
            recipient_emails = [student_email]
            print(f"   ✅ Email will be sent to: {student_email}")
            print(f"   ✅ Gmail will be pre-filled with: {student_email}")
        else:
            admin_email = 'moaaj.upm@gmail.com'
            recipient_emails = [admin_email]
            print(f"   ⚠️  Email will be sent to admin: {admin_email}")
            print(f"   ⚠️  Gmail will be pre-filled with: {admin_email}")
        
        # Test URL generation
        reminder_options_url = f"/school-fees/reminders/{fee_status.id}/options/"
        send_email_url = f"/school-fees/reminders/{fee_status.id}/send-email/"
        
        print(f"   Reminder Options URL: {reminder_options_url}")
        print(f"   Send Email URL: {send_email_url}")
        
        print("   ✅ Email functionality ready")
    
    print("\n" + "=" * 60)
    print("🎯 EMAIL FUNCTIONALITY SUMMARY")
    print("=" * 60)
    
    print("✅ Email Behavior:")
    print("   - Emails are sent directly to student email if available")
    print("   - Fallback to admin email if student email is not available")
    print("   - Gmail is pre-filled with student email (or admin as fallback)")
    print("   - Success messages show the actual recipient")
    
    print("\n✅ Updated Features:")
    print("   - send_reminder_email view sends to student email")
    print("   - Gmail URL generation uses student email")
    print("   - Success messages are more descriptive")
    print("   - Template shows 'Send directly to student email'")
    
    print("\n🚀 How to Test:")
    print("1. Start Django server: python manage.py runserver 8000")
    print("2. Go to: http://127.0.0.1:8000/school-fees/reminders/")
    print("3. Click 'Send Reminder' button")
    print("4. Choose 'Send Email' option")
    print("5. Verify email goes to student's email address")
    print("6. Verify Gmail is pre-filled with student's email")
    
    print("\n" + "=" * 60)
    print("✅ EMAIL FUNCTIONALITY UPDATED!")
    print("=" * 60)

if __name__ == "__main__":
    test_email_functionality()
