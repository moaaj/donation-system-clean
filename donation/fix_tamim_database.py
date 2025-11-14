#!/usr/bin/env python
"""
Directly fix Tamim's database record to Form 3
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from myapp.models import Student, FeeStructure, FeeStatus, Payment
from django.contrib.auth.models import User
from django.db import connection

def fix_tamim_database():
    """Directly fix Tamim's database record"""
    print("=" * 60)
    print("DIRECTLY FIXING TAMIM'S DATABASE RECORD")
    print("=" * 60)
    
    # Get Tamim's user and student record
    user = User.objects.filter(username='tamim123').first()
    if not user:
        print("❌ User 'tamim123' not found!")
        return
    
    student = user.myapp_profile.student
    print(f"✅ Student found: {student.first_name} {student.last_name}")
    
    # Show current level details
    print(f"\n📚 CURRENT LEVEL DETAILS:")
    print(f"   Level: {student.level}")
    print(f"   Level Custom: {student.level_custom}")
    print(f"   Display Value: {student.get_level_display_value()}")
    
    # Directly update the database
    print(f"\n🔧 DIRECTLY UPDATING DATABASE...")
    
    with connection.cursor() as cursor:
        # Update the student record directly
        cursor.execute("""
            UPDATE myapp_student 
            SET level = 'form', level_custom = 'Form 3' 
            WHERE id = %s
        """, [student.id])
        
        print(f"   ✅ Database updated directly")
    
    # Refresh the student object
    student.refresh_from_db()
    
    # Show updated level details
    print(f"\n📚 UPDATED LEVEL DETAILS:")
    print(f"   Level: {student.level}")
    print(f"   Level Custom: {student.level_custom}")
    print(f"   Display Value: {student.get_level_display_value()}")
    
    # Check what fees Form 3 students should see
    print(f"\n💰 FEES AVAILABLE FOR FORM 3:")
    
    form3_fees = FeeStructure.objects.filter(
        form__iexact='Form 3',
        is_active=True
    ).select_related('category')
    
    if form3_fees.exists():
        for fee in form3_fees:
            amount_display = f"RM {fee.amount}" if fee.amount else "Not set"
            if fee.frequency == 'monthly' and fee.total_amount and fee.monthly_duration:
                monthly_amount = fee.get_monthly_amount()
                amount_display = f"RM {fee.total_amount} over {fee.monthly_duration} months (Monthly: RM {monthly_amount})"
            
            print(f"   {fee.category.name}: {amount_display} ({fee.frequency})")
    else:
        print(f"   ❌ No fee structures found for Form 3")
    
    # Check if Tamim now has access to Form 3 fees
    print(f"\n🎯 CHECKING TAMIM'S ACCESS TO FORM 3 FEES:")
    
    tamim_level = student.get_level_display_value()
    print(f"   Tamim's level: {tamim_level}")
    
    # Try to get fees for Tamim's level
    available_fees = FeeStructure.objects.filter(
        form__iexact=tamim_level,
        is_active=True
    ).select_related('category')
    
    print(f"   Query: form__iexact='{tamim_level}'")
    print(f"   Found {available_fees.count()} fee structures")
    
    if available_fees.exists():
        print(f"   ✅ Tamim now has access to {available_fees.count()} fee structures:")
        for fee in available_fees:
            amount_display = f"RM {fee.amount}" if fee.amount else "Not set"
            if fee.frequency == 'monthly' and fee.total_amount and fee.monthly_duration:
                monthly_amount = fee.get_monthly_amount()
                amount_display = f"RM {fee.total_amount} over {fee.monthly_duration} months (Monthly: RM {monthly_amount})"
            
            print(f"     {fee.category.name}: {amount_display} ({fee.frequency})")
    else:
        print(f"   ❌ Still no fees available for {tamim_level}")
    
    # Show what fees Tamim should see in the student portal
    print(f"\n📱 WHAT TAMIM WILL SEE IN STUDENT PORTAL:")
    print(f"   When Tamim logs in to the student portal, he will see:")
    
    if available_fees.exists():
        for fee in available_fees:
            if fee.category.name == 'Tuition Fees':
                print(f"   🎓 Tuition Fees: RM {fee.amount} ({fee.frequency})")
            elif fee.category.name == 'Examination Fees':
                print(f"   📝 Examination Fees: RM {fee.amount} ({fee.frequency})")
            else:
                print(f"   📋 {fee.category.name}: RM {fee.amount} ({fee.frequency})")
        
        print(f"\n   💡 All Form 3 students see exactly the same fees:")
        print(f"   💡 This ensures fairness and consistency!")
    else:
        print(f"   ❌ No fees will be visible until fee structures are created for Form 3")
    
    print(f"\n" + "=" * 60)

if __name__ == '__main__':
    try:
        fix_tamim_database()
    except Exception as e:
        print(f"Error during fix: {str(e)}")
        import traceback
        traceback.print_exc()
