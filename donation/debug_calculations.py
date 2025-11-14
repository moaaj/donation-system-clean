#!/usr/bin/env python
"""
Debug script to identify why Amount Due and Achievement Percentage are showing 0
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from myapp.models import FeeStructure, Student, Payment, FeeStatus

def debug_calculations():
    print("🔍 Debugging Dashboard Calculations")
    print("=" * 50)
    
    # 1. Check Fee Structures
    print("\n1. FEE STRUCTURES:")
    all_fs = FeeStructure.objects.all()
    active_fs = FeeStructure.objects.filter(is_active=True)
    
    print(f"   Total Fee Structures: {all_fs.count()}")
    print(f"   Active Fee Structures: {active_fs.count()}")
    
    for fs in all_fs:
        print(f"   - Form: '{fs.form}', Amount: RM {fs.amount}, Active: {fs.is_active}")
    
    # 2. Check Student Forms
    print("\n2. STUDENT FORMS:")
    student_forms = Student.objects.values_list('level_custom', flat=True).distinct()
    print(f"   Available Forms: {list(student_forms)}")
    
    for form in student_forms:
        count = Student.objects.filter(level_custom=form, is_active=True).count()
        print(f"   - Form '{form}': {count} active students")
    
    # 3. Test Current Calculation Logic
    print("\n3. CURRENT CALCULATION LOGIC:")
    expected_amount = 0
    
    for fee_structure in active_fs:
        student_count = Student.objects.filter(
            level_custom=fee_structure.form,
            is_active=True
        ).count()
        contribution = fee_structure.amount * student_count
        expected_amount += contribution
        print(f"   Form '{fee_structure.form}': {student_count} students × RM {fee_structure.amount} = RM {contribution}")
    
    print(f"   Total Expected Amount: RM {expected_amount}")
    
    # 4. Check Payments
    print("\n4. PAYMENT DATA:")
    total_payments = Payment.objects.count()
    completed_payments = Payment.objects.filter(status='completed').count()
    actual_collection = Payment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
    
    print(f"   Total Payments: {total_payments}")
    print(f"   Completed Payments: {completed_payments}")
    print(f"   Actual Collection: RM {actual_collection}")
    
    # 5. Calculate Achievement
    achievement = (actual_collection / expected_amount * 100) if expected_amount > 0 else 0
    print(f"   Achievement Percentage: {achievement}%")
    
    # 6. Identify the Problem
    print("\n6. PROBLEM IDENTIFICATION:")
    if active_fs.count() == 0:
        print("   ❌ PROBLEM: No active fee structures!")
        print("   💡 SOLUTION: Activate fee structures or create new ones")
    elif expected_amount == 0:
        print("   ❌ PROBLEM: No students match fee structure forms!")
        print("   💡 SOLUTION: Fix form matching between fee structures and students")
    else:
        print("   ✅ Calculation logic appears correct")
    
    return {
        'expected_amount': expected_amount,
        'actual_collection': actual_collection,
        'achievement': achievement,
        'active_fee_structures': active_fs.count(),
        'total_students': Student.objects.filter(is_active=True).count()
    }

if __name__ == '__main__':
    from django.db.models import Sum
    result = debug_calculations()
    print(f"\n📊 SUMMARY: Expected: RM {result['expected_amount']}, Actual: RM {result['actual_collection']}, Achievement: {result['achievement']}%")
