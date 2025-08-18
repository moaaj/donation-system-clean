#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from myapp.models import Student, FeeStructure, FeeStatus, Payment
from django.contrib.auth.models import User
from django.utils import timezone

# Get the student
user = User.objects.filter(username='tamim123').first()
student = user.myapp_profile.student if user and hasattr(user, 'myapp_profile') else None

if student:
    print(f"Testing with student: {student.first_name} {student.last_name}")
    
    # Get the first fee structure
    fee = FeeStructure.objects.first()
    print(f"Testing with fee: {fee.category.name} - {fee.form}")
    
    # Check current status
    current_status = FeeStatus.objects.filter(student=student, fee_structure=fee).first()
    print(f"Current FeeStatus: {current_status.status if current_status else 'None'}")
    
    # Update to paid
    fee_status, created = FeeStatus.objects.get_or_create(
        student=student,
        fee_structure=fee,
        defaults={
            'amount': fee.amount,
            'due_date': timezone.now().date(),
            'status': 'paid'
        }
    )
    
    if not created:
        fee_status.status = 'paid'
        fee_status.save()
    
    print(f"Updated FeeStatus to: {fee_status.status}")
    print("Test completed!")
else:
    print("Student not found!")
