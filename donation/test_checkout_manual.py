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
    print(f"Testing manual checkout for student: {student.first_name} {student.last_name}")
    
    # Get the fee that's in the cart (fee ID 11)
    fee = FeeStructure.objects.get(id=11)
    print(f"Processing fee: {fee.category.name} - {fee.form}")
    
    # Check current FeeStatus
    fee_statuses = FeeStatus.objects.filter(student=student, fee_structure=fee)
    print(f"Current FeeStatus records: {fee_statuses.count()}")
    for status in fee_statuses:
        print(f"- ID {status.id}: {status.status}")
    
    # Simulate checkout process
    print("\nSimulating checkout...")
    
    # Create payment
    payment = Payment.objects.create(
        student=student,
        fee_structure=fee,
        amount=fee.amount,
        payment_date=timezone.now().date(),
        payment_method='online',
        status='completed'
    )
    print(f"Created payment: {payment.id}")
    
    # Update FeeStatus for monthly fees
    if fee.frequency == 'monthly':
        pending_statuses = FeeStatus.objects.filter(
            student=student,
            fee_structure=fee,
            status__in=['pending', 'overdue']
        )
        print(f"Found {pending_statuses.count()} pending FeeStatus records")
        pending_statuses.update(status='paid')
        print("Updated all pending FeeStatus records to paid")
    else:
        # For non-monthly fees
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
        print(f"Updated FeeStatus to paid")
    
    # Check final status
    final_statuses = FeeStatus.objects.filter(student=student, fee_structure=fee)
    print(f"\nFinal FeeStatus records:")
    for status in final_statuses:
        print(f"- ID {status.id}: {status.status}")
    
    print("\nCheckout simulation completed!")
else:
    print("Student not found!")
