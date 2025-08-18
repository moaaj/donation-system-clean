#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from myapp.models import Student, FeeStructure, FeeStatus
from django.contrib.auth.models import User

# Get the student
user = User.objects.filter(username='tamim123').first()
student = user.myapp_profile.student if user and hasattr(user, 'myapp_profile') else None

if student:
    print(f"Checking School Fees for student: {student.first_name} {student.last_name}")
    
    # Get School Fees
    try:
        school_fee = FeeStructure.objects.get(category__name='School Fees')
        print(f"School Fees found: ID {school_fee.id}, Amount: {school_fee.amount}")
        
        # Check FeeStatus
        fee_status = FeeStatus.objects.filter(student=student, fee_structure=school_fee).first()
        print(f"FeeStatus: {fee_status.status if fee_status else 'None'}")
        
        # Check all FeeStatus records for this student
        all_statuses = FeeStatus.objects.filter(student=student)
        print(f"All FeeStatus records for this student:")
        for status in all_statuses:
            print(f"- {status.fee_structure.category.name}: {status.status}")
            
    except FeeStructure.DoesNotExist:
        print("School Fees not found")
else:
    print("Student not found!")
