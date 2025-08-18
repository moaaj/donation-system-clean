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
    print(f"Debugging School Fees for student: {student.first_name} {student.last_name}")
    
    # Get School Fees
    school_fee = FeeStructure.objects.get(category__name='School Fees')
    print(f"School Fees details:")
    print(f"- ID: {school_fee.id}")
    print(f"- Amount: {school_fee.amount}")
    print(f"- Frequency: {school_fee.frequency}")
    print(f"- Total Amount: {school_fee.total_amount}")
    print(f"- Monthly Duration: {school_fee.monthly_duration}")
    
    # Check all FeeStatus records for School Fees
    school_fee_statuses = FeeStatus.objects.filter(student=student, fee_structure=school_fee)
    print(f"\nSchool Fees FeeStatus records: {school_fee_statuses.count()}")
    for i, status in enumerate(school_fee_statuses):
        print(f"- Record {i+1}: ID {status.id}, Status: {status.status}, Amount: {status.amount}, Due Date: {status.due_date}")
    
    # Check payments for School Fees
    school_fee_payments = Payment.objects.filter(student=student, fee_structure=school_fee)
    print(f"\nSchool Fees Payment records: {school_fee_payments.count()}")
    for payment in school_fee_payments:
        print(f"- Payment ID: {payment.id}, Amount: {payment.amount}, Status: {payment.status}, Date: {payment.payment_date}")
    
    # Simulate what happens during checkout
    print(f"\nSimulating checkout for School Fees...")
    
    # Create payment
    payment = Payment.objects.create(
        student=student,
        fee_structure=school_fee,
        amount=school_fee.amount,
        payment_date=timezone.now().date(),
        payment_method='online',
        status='completed'
    )
    print(f"Created payment: {payment.id}")
    
    # Update FeeStatus
    fee_status, created = FeeStatus.objects.get_or_create(
        student=student,
        fee_structure=school_fee,
        defaults={
            'amount': school_fee.amount,
            'due_date': timezone.now().date(),
            'status': 'paid'
        }
    )
    
    if not created:
        fee_status.status = 'paid'
        fee_status.save()
        print(f"Updated existing FeeStatus {fee_status.id} to paid")
    else:
        print(f"Created new FeeStatus {fee_status.id} with status paid")
    
    # Check final status
    final_statuses = FeeStatus.objects.filter(student=student, fee_structure=school_fee)
    print(f"\nFinal School Fees FeeStatus records:")
    for status in final_statuses:
        print(f"- ID {status.id}: {status.status}")
        
else:
    print("Student not found!")
