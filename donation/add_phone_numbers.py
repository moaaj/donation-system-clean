#!/usr/bin/env python
"""
Add phone numbers to students for testing text message functionality
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from myapp.models import Student, UserProfile, FeeCategory, FeeStructure, FeeStatus, IndividualStudentFee, FeeWaiver, Payment, Parent
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta

def add_phone_numbers():
    """Add phone numbers to students for testing"""
    
    print("📱 Adding Phone Numbers to Students")
    print("=" * 70)
    
    # Get all active students
    students = Student.objects.filter(is_active=True)
    
    # Sample phone numbers for testing
    test_phones = [
        '+60123456789',  # Tamim Student
        '+60123456790',  # Taskin Ahmed
        '+60123456791',  # Sabbir Rahman
        '+60123456792',  # Taijul Islam
    ]
    
    updated_count = 0
    
    for i, student in enumerate(students):
        if i < len(test_phones):
            # Find or create a parent for this student
            parent, created = Parent.objects.get_or_create(
                user=User.objects.first(),  # Use first user as default
                defaults={
                    'nric': f'P{i+1:06d}',
                    'phone_number': test_phones[i],
                    'address': 'Test Address'
                }
            )
            
            # Add student to parent if not already associated
            if student not in parent.students.all():
                parent.students.add(student)
            
            # Update phone number if needed
            if parent.phone_number != test_phones[i]:
                parent.phone_number = test_phones[i]
                parent.save()
            
            updated_count += 1
            
            print(f"✅ Added phone {test_phones[i]} to {student.first_name} {student.last_name} via parent")
    
    print(f"\n🎉 Updated {updated_count} students with phone numbers")
    
    # Verify the updates
    print("\n" + "=" * 70)
    print("📋 VERIFICATION")
    print("=" * 70)
    
    students_with_parents = Student.objects.filter(is_active=True, parents__isnull=False)
    print(f"📊 Students with parent phone numbers: {students_with_parents.count()}")
    
    for student in students_with_parents:
        parent = student.parents.first()
        if parent:
            print(f"👤 {student.first_name} {student.last_name}: {parent.phone_number}")
    
    print("\n" + "=" * 70)
    print("🎯 TEXT MESSAGE FUNCTIONALITY STATUS")
    print("=" * 70)
    
    if students_with_parents.count() > 0:
        print("✅ Students now have parent phone numbers for text message testing")
        print("✅ Text message functionality will be available in payment reminders")
        print("ℹ️  Note: Text messages are currently logged to console (placeholder)")
        print("ℹ️  To enable actual SMS, integrate with Twilio, AWS SNS, or local gateway")
    else:
        print("⚠️  No students have parent phone numbers")
    
    print("\n" + "=" * 70)
    print("🚀 NEXT STEPS")
    print("=" * 70)
    
    print("1. Test the 'Send Reminder' functionality in the Payment Reminders dashboard")
    print("2. Check console output for text message content")
    print("3. Verify email reminders are working correctly")
    print("4. Test 'Generate Letter' functionality")
    print("5. Consider integrating with actual SMS service for production use")

if __name__ == "__main__":
    add_phone_numbers()
