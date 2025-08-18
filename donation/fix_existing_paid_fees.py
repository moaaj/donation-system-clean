#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from myapp.models import Student, FeeStructure, FeeStatus, Payment
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

# Get the student
user = User.objects.filter(username='tamim123').first()
student = user.myapp_profile.student if user and hasattr(user, 'myapp_profile') else None

if student:
    print(f"Student: {student.first_name} {student.last_name}")
    
    # Get all active fees
    fees = FeeStructure.objects.filter(is_active=True)
    print(f"Active fees: {fees.count()}")
    
    # For each fee, check if there are payments but no FeeStatus records
    for fee in fees:
        payments = Payment.objects.filter(student=student, fee_structure=fee)
        statuses = FeeStatus.objects.filter(student=student, fee_structure=fee)
        
        print(f"\nFee {fee.id} ({fee.category.name}):")
        print(f"  Payments: {payments.count()}")
        print(f"  FeeStatus records: {statuses.count()}")
        
        if payments.exists() and not statuses.exists():
            print(f"  Creating FeeStatus records for paid fees...")
            
            if fee.frequency == 'monthly':
                # For monthly fees, create multiple FeeStatus records
                monthly_amount = fee.get_monthly_amount()
                start_date = timezone.now().date()
                
                for month in range(fee.monthly_duration):
                    due_date = start_date + timedelta(days=30 * month)
                    
                    # Create FeeStatus record
                    fee_status = FeeStatus.objects.create(
                        student=student,
                        fee_structure=fee,
                        amount=monthly_amount,
                        due_date=due_date,
                        status='paid'  # Mark as paid immediately
                    )
                    print(f"    Created FeeStatus record {fee_status.id} for month {month + 1}")
                
                print(f"  Created {fee.monthly_duration} FeeStatus records for monthly fee")
            else:
                # For non-monthly fees, create one FeeStatus record
                FeeStatus.objects.create(
                    student=student,
                    fee_structure=fee,
                    amount=fee.amount,
                    due_date=timezone.now().date(),
                    status='paid'
                )
                print(f"  Created 1 FeeStatus record")
    
    print(f"\nFinal status:")
    for fee in fees:
        statuses = FeeStatus.objects.filter(student=student, fee_structure=fee)
        print(f"Fee {fee.id} ({fee.category.name}): {statuses.count()} status records - {[s.status for s in statuses]}")
    
else:
    print("Student not found!")
