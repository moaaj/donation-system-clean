#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from myapp.models import Student, Parent, FeeStructure, FeeStatus, Payment
from django.contrib.auth.models import User

def test_fee_filtering():
    """Test the fee filtering logic for a specific parent/child"""
    
    print("=" * 60)
    print("TESTING FEE FILTERING LOGIC")
    print("=" * 60)
    
    # Find a parent with children
    parent = Parent.objects.filter(students__isnull=False).first()
    if not parent:
        print("No parent with children found!")
        return
    
    print(f"Testing with parent: {parent.user.get_full_name()}")
    
    for child in parent.students.filter(is_active=True):
        print(f"\n📚 Child: {child.first_name} {child.last_name}")
        print(f"   Level: {child.level}")
        print(f"   Level Custom: {child.level_custom}")
        print(f"   Display Value: {child.get_level_display_value()}")
        
        # Get available fee structures
        student_level = child.get_level_display_value()
        available_fees = FeeStructure.objects.filter(
            form__iexact=student_level,
            is_active=True
        ).select_related('category')
        
        print(f"   Available fees for level '{student_level}': {available_fees.count()}")
        
        for fee in available_fees:
            print(f"\n   💰 Fee: {fee.category.name} (Form {fee.form})")
            
            # Check existing FeeStatus records
            existing_statuses = FeeStatus.objects.filter(
                student=child,
                fee_structure=fee
            )
            
            print(f"      FeeStatus records: {existing_statuses.count()}")
            if existing_statuses.exists():
                for status in existing_statuses:
                    print(f"      - Status: {status.status}, Amount: {status.amount}, Due: {status.due_date}")
            
            # Check payments
            payments = Payment.objects.filter(
                student=child,
                fee_structure=fee,
                status='completed'
            )
            print(f"      Completed payments: {payments.count()}")
            
            # Apply filtering logic
            if not existing_statuses.exists():
                result = "SHOW (no FeeStatus)"
            else:
                unpaid_statuses = existing_statuses.filter(status__in=['pending', 'overdue'])
                if unpaid_statuses.exists():
                    result = "SHOW (has unpaid status)"
                else:
                    result = "HIDE (all paid)"
            
            print(f"      Result: {result}")

if __name__ == "__main__":
    test_fee_filtering()
