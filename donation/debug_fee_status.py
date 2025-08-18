#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from myapp.models import Student, FeeStructure, FeeStatus, Payment
from django.contrib.auth.models import User

# Get the student
user = User.objects.filter(username='tamim123').first()
student = user.myapp_profile.student if user and hasattr(user, 'myapp_profile') else None

if student:
    print(f"Student: {student.first_name} {student.last_name}")
    
    # Get all active fees
    fees = FeeStructure.objects.filter(is_active=True)
    print(f"Active fees: {fees.count()}")
    
    # Check each fee's status
    for fee in fees:
        statuses = FeeStatus.objects.filter(student=student, fee_structure=fee)
        print(f"Fee {fee.id} ({fee.category.name}): {statuses.count()} status records - {[s.status for s in statuses]}")
    
    # Check payments
    payments = Payment.objects.filter(student=student)
    print(f"\nPayments: {payments.count()}")
    for payment in payments:
        if payment.fee_structure:
            print(f"Payment {payment.id}: {payment.fee_structure.category.name} - {payment.amount}")
        else:
            print(f"Payment {payment.id}: Individual fee - {payment.amount}")
    
    # Check cart
    print(f"\nCart should be empty now")
else:
    print("Student not found!")
