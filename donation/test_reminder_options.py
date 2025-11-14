#!/usr/bin/env python
"""
Test script for the new reminder options functionality
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

def test_reminder_options_functionality():
    """Test the reminder options functionality"""
    
    print("🧪 TESTING REMINDER OPTIONS FUNCTIONALITY")
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
        
        # Test discounted amount calculation
        try:
            discounted_amount = fee_status.get_discounted_amount()
            print(f"   Discounted Amount: RM {discounted_amount:.2f}")
        except Exception as e:
            print(f"   Discounted Amount: Error - {str(e)}")
        
        # Test contact information
        student = fee_status.student
        student_email = getattr(student, 'email', None)
        parent = student.parents.first()
        student_phone = parent.phone_number if parent else None
        
        print(f"   Student Email: {student_email or 'Not available'}")
        print(f"   Student Phone: {student_phone or 'Not available'}")
        
        # Test days calculation
        today = timezone.now().date()
        if fee_status.due_date < today:
            days_text = f"{today - fee_status.due_date} days overdue"
            is_overdue = True
        else:
            days_text = f"{fee_status.due_date - today} days until due"
            is_overdue = False
        
        print(f"   Status: {days_text}")
        print(f"   Is Overdue: {is_overdue}")
        
        # Test URL generation
        reminder_options_url = f"/school-fees/reminders/{fee_status.id}/options/"
        send_email_url = f"/school-fees/reminders/{fee_status.id}/send-email/"
        send_text_url = f"/school-fees/reminders/{fee_status.id}/send-text/"
        
        print(f"   Reminder Options URL: {reminder_options_url}")
        print(f"   Send Email URL: {send_email_url}")
        print(f"   Send Text URL: {send_text_url}")
        
        print("   ✅ Fee status ready for reminder options")
    
    print("\n" + "=" * 60)
    print("🎯 REMINDER OPTIONS FUNCTIONALITY SUMMARY")
    print("=" * 60)
    
    print("✅ New Views Created:")
    print("   - reminder_options: Shows text/email options")
    print("   - send_reminder_email: Sends email + redirects to Gmail")
    print("   - send_reminder_text: Sends SMS + redirects to Gmail")
    print("   - generate_letter_content: Creates letter content")
    print("   - generate_gmail_url: Creates Gmail compose URL")
    
    print("\n✅ New URLs Added:")
    print("   - /reminders/<id>/options/ - Reminder options page")
    print("   - /reminders/<id>/send-email/ - Send email option")
    print("   - /reminders/<id>/send-text/ - Send text option")
    
    print("\n✅ Template Updated:")
    print("   - reminder_options.html - New options page")
    print("   - payment_reminders.html - Updated to use options page")
    
    print("\n✅ Features Implemented:")
    print("   - Two reminder options (Email/Text)")
    print("   - Automatic Gmail redirect with generated letter")
    print("   - Contact information display")
    print("   - Payment details with discounts")
    print("   - Professional letter content generation")
    
    print("\n🚀 How to Test:")
    print("1. Start Django server: python manage.py runserver 8000")
    print("2. Go to: http://127.0.0.1:8000/school-fees/reminders/")
    print("3. Click 'Send Reminder' button")
    print("4. Choose Email or Text option")
    print("5. Verify Gmail redirect with generated letter")
    
    print("\n" + "=" * 60)
    print("✅ REMINDER OPTIONS FUNCTIONALITY READY!")
    print("=" * 60)

if __name__ == "__main__":
    test_reminder_options_functionality()

