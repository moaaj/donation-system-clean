#!/usr/bin/env python
"""
Test script for the Form-Based Fee System

This script demonstrates how the new form-based fee system works,
ensuring that all students in the same form pay the same amount.
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from myapp.models import Student, FeeCategory, FeeStructure, FeeStatus, Payment
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

def test_form_based_fee_system():
    """Test the form-based fee system"""
    print("=" * 60)
    print("TESTING FORM-BASED FEE SYSTEM")
    print("=" * 60)
    
    # 1. Check existing students and their form levels
    print("\n1. CHECKING STUDENT FORM LEVELS")
    print("-" * 40)
    
    students = Student.objects.filter(is_active=True)
    form_counts = {}
    
    for student in students:
        level = student.get_level_display_value()
        form_counts[level] = form_counts.get(level, 0) + 1
        print(f"  {student.first_name} {student.last_name}: {level}")
    
    print(f"\nForm Distribution:")
    for form, count in sorted(form_counts.items()):
        print(f"  {form}: {count} students")
    
    # 2. Check existing fee structures
    print("\n2. CHECKING EXISTING FEE STRUCTURES")
    print("-" * 40)
    
    fee_structures = FeeStructure.objects.filter(is_active=True).select_related('category')
    
    if not fee_structures.exists():
        print("  No fee structures found.")
        print("  Creating sample fee structures for testing...")
        create_sample_fee_structures()
        fee_structures = FeeStructure.objects.filter(is_active=True).select_related('category')
    
    for fs in fee_structures.order_by('form', 'category__name'):
        amount_display = f"RM {fs.amount}" if fs.amount else "Not set"
        if fs.frequency == 'monthly' and fs.total_amount and fs.monthly_duration:
            amount_display = f"RM {fs.total_amount} over {fs.monthly_duration} months"
        
        print(f"  {fs.category.name} - {fs.form}: {amount_display} ({fs.frequency})")
    
    # 3. Test fee structure retrieval for specific students
    print("\n3. TESTING FEE STRUCTURE RETRIEVAL")
    print("-" * 40)
    
    for student in students[:3]:  # Test with first 3 students
        student_level = student.get_level_display_value()
        print(f"\n  Student: {student.first_name} {student.last_name} ({student_level})")
        
        # Get fee structures for this student's form level
        available_fees = FeeStructure.objects.filter(
            form__iexact=student_level,
            is_active=True
        ).select_related('category')
        
        if available_fees.exists():
            print(f"    Available fees:")
            for fee in available_fees:
                amount_display = f"RM {fee.amount}" if fee.amount else "Not set"
                if fee.frequency == 'monthly' and fee.total_amount and fee.monthly_duration:
                    monthly_amount = fee.get_monthly_amount()
                    amount_display = f"RM {fee.total_amount} over {fee.monthly_duration} months (Monthly: RM {monthly_amount})"
                
                print(f"      {fee.category.name}: {amount_display} ({fee.frequency})")
        else:
            print(f"    No fees available for {student_level}")
    
    # 4. Test the get_for_student method
    print("\n4. TESTING get_for_student METHOD")
    print("-" * 40)
    
    for student in students[:3]:
        student_level = student.get_level_display_value()
        print(f"\n  Student: {student.first_name} {student.last_name} ({student_level})")
        
        # Test getting fee structure for specific category
        # First get the category, then use get_for_student
        tuition_category = FeeCategory.objects.filter(name__icontains='Tuition').first()
        if tuition_category:
            tuition_fee = FeeStructure.get_for_student(student, category=tuition_category)
            if tuition_fee:
                print(f"    Tuition Fee: RM {tuition_fee.amount} ({tuition_fee.frequency})")
            else:
                print(f"    No tuition fee found for {student_level}")
        else:
            print(f"    No tuition category found")
    
    # 5. Check fee statuses and ensure consistency
    print("\n5. CHECKING FEE STATUS CONSISTENCY")
    print("-" * 40)
    
    fee_statuses = FeeStatus.objects.select_related('student', 'fee_structure', 'fee_structure__category')
    
    if fee_statuses.exists():
        # Group by fee structure to check consistency
        fee_structure_groups = {}
        for status in fee_statuses:
            key = (status.fee_structure.category.name, status.fee_structure.form)
            if key not in fee_structure_groups:
                fee_structure_groups[key] = []
            fee_structure_groups[key].append(status)
        
        for (category, form), statuses in fee_structure_groups.items():
            print(f"\n  {category} - {form}:")
            amounts = set()
            for status in statuses:
                amounts.add(status.amount)
                print(f"    {status.student.first_name} {status.student.last_name}: RM {status.amount}")
            
            if len(amounts) == 1:
                print(f"    ✓ All students pay the same amount: RM {list(amounts)[0]}")
            else:
                print(f"    ⚠ Inconsistent amounts found: {amounts}")
    else:
        print("  No fee statuses found.")
    
    print("\n" + "=" * 60)
    print("FORM-BASED FEE SYSTEM TEST COMPLETED")
    print("=" * 60)

def create_sample_fee_structures():
    """Create sample fee structures for testing"""
    print("  Creating sample fee structures...")
    
    # Create fee categories if they don't exist
    tuition_category, _ = FeeCategory.objects.get_or_create(
        name='Tuition Fees',
        defaults={'description': 'Annual tuition fees', 'category_type': 'general'}
    )
    
    exam_category, _ = FeeCategory.objects.get_or_create(
        name='Examination Fees',
        defaults={'description': 'Term examination fees', 'category_type': 'general'}
    )
    
    # Create fee structures for different forms
    forms = ['Form 1', 'Form 2', 'Form 3', 'Form 4', 'Form 5']
    
    for i, form in enumerate(forms):
        # Tuition fees increase by form level
        tuition_amount = Decimal('2000') + (i * Decimal('500'))
        
        # Create or update tuition fee structure
        tuition_fee, created = FeeStructure.objects.get_or_create(
            category=tuition_category,
            form=form,
            defaults={
                'amount': tuition_amount,
                'frequency': 'yearly',
                'is_active': True
            }
        )
        
        if created:
            print(f"    Created tuition fee for {form}: RM {tuition_amount}")
        else:
            tuition_fee.amount = tuition_amount
            tuition_fee.save()
            print(f"    Updated tuition fee for {form}: RM {tuition_amount}")
        
        # Create examination fees (same for all forms)
        exam_fee, created = FeeStructure.objects.get_or_create(
            category=exam_category,
            form=form,
            defaults={
                'amount': Decimal('300'),
                'frequency': 'termly',
                'is_active': True
            }
        )
        
        if created:
            print(f"    Created examination fee for {form}: RM 300")
    
    print("  Sample fee structures created successfully!")

def setup_students_for_testing():
    """Set up students with proper form levels for testing"""
    print("\n  Setting up students with proper form levels for testing...")
    
    # Update existing students to have proper form levels
    students = Student.objects.filter(is_active=True)
    
    # Assign students to different forms for testing
    form_assignments = [
        ('Tamim Iqbal', 'Form 3'),
        ('Test Student', 'Form 2'),
        ('Tamim Student', 'Form 1'),
        ('Nasir Hossain', 'Form 4'),
    ]
    
    for student_name, form_level in form_assignments:
        try:
            student = Student.objects.filter(first_name__icontains=student_name.split()[0]).first()
            if student:
                student.level = 'form'
                student.level_custom = form_level
                student.save()
                print(f"    Updated {student.first_name} {student.last_name} to {form_level}")
        except Exception as e:
            print(f"    Error updating {student_name}: {str(e)}")
    
    print("  Student form levels updated for testing!")

if __name__ == '__main__':
    try:
        test_form_based_fee_system()
        
        # Ask if user wants to set up students for testing
        print("\n" + "=" * 60)
        print("SETUP OPTIONS")
        print("=" * 60)
        print("The test shows that students don't have proper form levels set up.")
        print("To properly test the form-based fee system, you can:")
        print("1. Run the management command: python manage.py setup_form_based_fees --list-forms")
        print("2. Update student form levels in the admin panel")
        print("3. Or run this script again after setting up students")
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
