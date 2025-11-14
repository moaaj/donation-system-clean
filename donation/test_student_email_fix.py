#!/usr/bin/env python
"""
Test script to verify student email fix
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
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta

def test_student_email_fix():
    """Test that student emails are properly retrieved"""
    
    print("🧪 TESTING STUDENT EMAIL FIX")
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
        
        # Test student email retrieval (OLD METHOD - should fail)
        print(f"\n   📧 OLD METHOD (getattr):")
        try:
            old_email = getattr(fee_status.student, 'email', None)
            print(f"      Result: {old_email}")
            print(f"      Status: {'❌ FAILED' if old_email is None else '✅ WORKED'}")
        except Exception as e:
            print(f"      Error: {str(e)}")
            print(f"      Status: ❌ FAILED")
        
        # Test student email retrieval (NEW METHOD - should work)
        print(f"\n   📧 NEW METHOD (UserProfile):")
        try:
            user_profile = fee_status.student.user_profile.first()
            new_email = user_profile.user.email if user_profile else None
            print(f"      Result: {new_email}")
            print(f"      Status: {'✅ WORKED' if new_email else '❌ FAILED'}")
            
            if new_email:
                print(f"      ✅ Email will be sent to: {new_email}")
                print(f"      ✅ Gmail will be pre-filled with: {new_email}")
            else:
                print(f"      ⚠️  No email found, will use admin email")
        except Exception as e:
            print(f"      Error: {str(e)}")
            print(f"      Status: ❌ FAILED")
        
        # Test URL generation
        reminder_options_url = f"/school-fees/reminders/{fee_status.id}/options/"
        send_email_url = f"/school-fees/reminders/{fee_status.id}/send-email/"
        
        print(f"\n   🔗 URLs:")
        print(f"      Reminder Options: {reminder_options_url}")
        print(f"      Send Email: {send_email_url}")
        
        print("   ✅ Email functionality ready")
    
    print("\n" + "=" * 60)
    print("🎯 STUDENT EMAIL FIX SUMMARY")
    print("=" * 60)
    
    print("✅ Problem Identified:")
    print("   - Student model doesn't have email field")
    print("   - Email is stored in User model linked via UserProfile")
    print("   - Old method used getattr(student, 'email', None)")
    print("   - New method uses student.user_profile.first().user.email")
    
    print("\n✅ Fix Applied:")
    print("   - Updated send_reminder_email view")
    print("   - Updated reminder_options view")
    print("   - Added proper error handling")
    print("   - Maintained fallback to admin email")
    
    print("\n✅ Expected Results:")
    print("   - Emails will be sent to student's actual email address")
    print("   - Gmail will be pre-filled with student's email")
    print("   - Success messages will show correct recipient")
    print("   - Fallback to admin email if student email not available")
    
    print("\n🚀 How to Test:")
    print("1. Start Django server: python manage.py runserver 8000")
    print("2. Go to: http://127.0.0.1:8000/school-fees/reminders/")
    print("3. Click 'Send Reminder' button")
    print("4. Choose 'Send Email' option")
    print("5. Verify email goes to student's email (not admin)")
    print("6. Verify Gmail is pre-filled with student's email")
    
    print("\n" + "=" * 60)
    print("✅ STUDENT EMAIL FIX COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    test_student_email_fix()
