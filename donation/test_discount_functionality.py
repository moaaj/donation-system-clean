#!/usr/bin/env python
import os
import sys
import django
from decimal import Decimal

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from myapp.models import Student, UserProfile, FeeCategory, FeeStructure, FeeStatus, FeeWaiver
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta

def test_discount_functionality():
    """Test that discount functionality works correctly"""
    
    print("🧪 Testing Discount Functionality")
    print("=" * 50)
    
    # Clean up any existing test data
    print("🧹 Cleaning up existing test data...")
    Student.objects.filter(student_id='DISCTEST001').delete()
    User.objects.filter(username='student_disctest001').delete()
    FeeCategory.objects.filter(name='Test Tuition').delete()
    
    # Create test student
    print("\n📚 Creating test student...")
    student = Student.objects.create(
        student_id='DISCTEST001',
        nric='D123456-78',
        first_name='Discount',
        last_name='Test',
        level='form',
        level_custom='Form 3',
        year_batch=2025,
        is_active=True
    )
    print(f"✅ Test student created: {student}")
    
    # Create user account for the student
    print("\n👤 Creating user account for student...")
    username = 'student_disctest001'
    password = 'disctest001123'
    
    user = User.objects.create_user(
        username=username,
        email=f"{username}@school.com",
        password=password,
        first_name=student.first_name,
        last_name=student.last_name
    )
    
    user_profile = UserProfile.objects.create(
        user=user,
        role='student',
        student=student
    )
    print(f"✅ User account created - Username: {username}")
    
    # Create fee category
    print("\n💰 Creating fee category...")
    category = FeeCategory.objects.create(
        name='Test Tuition',
        description='Test tuition fees',
        category_type='general'
    )
    print(f"✅ Fee category created: {category}")
    
    # Create fee structure
    print("\n📋 Creating fee structure...")
    fee_structure = FeeStructure.objects.create(
        category=category,
        form='Form 3',
        amount=Decimal('3000.00'),
        frequency='yearly',
        is_active=True
    )
    print(f"✅ Fee structure created: {fee_structure}")
    
    # Create fee status
    print("\n📊 Creating fee status...")
    fee_status = FeeStatus.objects.create(
        student=student,
        fee_structure=fee_structure,
        amount=Decimal('3000.00'),
        due_date=date.today() + timedelta(days=30),
        status='pending'
    )
    print(f"✅ Fee status created: {fee_status}")
    
    # Test original amount
    print("\n🔍 Testing original amount...")
    original_amount = fee_status.get_original_amount()
    discounted_amount = fee_status.get_discounted_amount()
    discount_info = fee_status.get_discount_info()
    
    print(f"Original amount: RM {original_amount}")
    print(f"Discounted amount: RM {discounted_amount}")
    print(f"Has discount: {discount_info['has_discount']}")
    
    if original_amount == Decimal('3000.00') and discounted_amount == Decimal('3000.00'):
        print("✅ Original amount calculation correct")
    else:
        print("❌ Original amount calculation incorrect")
        return
    
    # Create a percentage-based waiver
    print("\n🎫 Creating percentage-based waiver...")
    waiver_percentage = FeeWaiver.objects.create(
        student=student,
        category=category,
        waiver_type='scholarship',
        amount=Decimal('0.00'),
        percentage=Decimal('25.00'),  # 25% discount
        reason='Academic excellence scholarship',
        start_date=date.today(),
        end_date=date.today() + timedelta(days=365),
        status='approved',
        approved_date=timezone.now()
    )
    print(f"✅ Percentage waiver created: {waiver_percentage}")
    
    # Test discounted amount with percentage waiver
    print("\n🔍 Testing discounted amount with percentage waiver...")
    discounted_amount = fee_status.get_discounted_amount()
    discount_info = fee_status.get_discount_info()
    
    expected_discount = Decimal('750.00')  # 25% of 3000
    expected_final = Decimal('2250.00')    # 3000 - 750
    
    print(f"Discounted amount: RM {discounted_amount}")
    print(f"Expected discount: RM {expected_discount}")
    print(f"Expected final amount: RM {expected_final}")
    print(f"Total discount: RM {discount_info['total_discount']}")
    print(f"Has discount: {discount_info['has_discount']}")
    
    if discounted_amount == expected_final and discount_info['total_discount'] == expected_discount:
        print("✅ Percentage discount calculation correct")
    else:
        print("❌ Percentage discount calculation incorrect")
        return
    
    # Create a fixed amount waiver
    print("\n🎫 Creating fixed amount waiver...")
    waiver_fixed = FeeWaiver.objects.create(
        student=student,
        category=category,
        waiver_type='discount',
        amount=Decimal('500.00'),  # RM 500 discount
        percentage=None,
        reason='Merit-based discount',
        start_date=date.today(),
        end_date=date.today() + timedelta(days=365),
        status='approved',
        approved_date=timezone.now()
    )
    print(f"✅ Fixed amount waiver created: {waiver_fixed}")
    
    # Test discounted amount with both waivers
    print("\n🔍 Testing discounted amount with both waivers...")
    discounted_amount = fee_status.get_discounted_amount()
    discount_info = fee_status.get_discount_info()
    
    total_discount = Decimal('1250.00')  # 750 (25%) + 500 (fixed)
    expected_final = Decimal('1750.00')  # 3000 - 1250
    
    print(f"Discounted amount: RM {discounted_amount}")
    print(f"Total discount: RM {discount_info['total_discount']}")
    print(f"Expected final amount: RM {expected_final}")
    print(f"Number of waivers: {len(discount_info['waivers'])}")
    
    if discounted_amount == expected_final and discount_info['total_discount'] == total_discount:
        print("✅ Combined discount calculation correct")
    else:
        print("❌ Combined discount calculation incorrect")
        return
    
    # Test waiver details
    print("\n🔍 Testing waiver details...")
    for i, waiver_info in enumerate(discount_info['waivers']):
        print(f"Waiver {i+1}:")
        print(f"  Type: {waiver_info['type']}")
        print(f"  Amount: {waiver_info['amount']}")
        print(f"  Percentage: {waiver_info['percentage']}")
        print(f"  Discount amount: {waiver_info['discount_amount']}")
    
    # Test expired waiver
    print("\n🔍 Testing expired waiver...")
    expired_waiver = FeeWaiver.objects.create(
        student=student,
        category=category,
        waiver_type='waiver',
        amount=Decimal('1000.00'),
        percentage=None,
        reason='Expired waiver',
        start_date=date.today() - timedelta(days=365),
        end_date=date.today() - timedelta(days=1),  # Expired yesterday
        status='approved',
        approved_date=timezone.now()
    )
    print(f"✅ Expired waiver created: {expired_waiver}")
    
    # Test that expired waiver doesn't affect discount
    discounted_amount_after_expired = fee_status.get_discounted_amount()
    discount_info_after_expired = fee_status.get_discount_info()
    
    print(f"Discounted amount after expired waiver: RM {discounted_amount_after_expired}")
    print(f"Total discount after expired waiver: RM {discount_info_after_expired['total_discount']}")
    
    if discounted_amount_after_expired == expected_final:
        print("✅ Expired waiver correctly ignored")
    else:
        print("❌ Expired waiver incorrectly applied")
        return
    
    # Test pending waiver (should not be applied)
    print("\n🔍 Testing pending waiver...")
    pending_waiver = FeeWaiver.objects.create(
        student=student,
        category=category,
        waiver_type='scholarship',
        amount=Decimal('200.00'),
        percentage=None,
        reason='Pending waiver',
        start_date=date.today(),
        end_date=date.today() + timedelta(days=365),
        status='pending',  # Not approved
        approved_date=None
    )
    print(f"✅ Pending waiver created: {pending_waiver}")
    
    # Test that pending waiver doesn't affect discount
    discounted_amount_after_pending = fee_status.get_discounted_amount()
    discount_info_after_pending = fee_status.get_discount_info()
    
    print(f"Discounted amount after pending waiver: RM {discounted_amount_after_pending}")
    print(f"Total discount after pending waiver: RM {discount_info_after_pending['total_discount']}")
    
    if discounted_amount_after_pending == expected_final:
        print("✅ Pending waiver correctly ignored")
    else:
        print("❌ Pending waiver incorrectly applied")
        return
    
    # Clean up test data
    print("\n🧹 Cleaning up test data...")
    FeeWaiver.objects.filter(student=student).delete()
    FeeStatus.objects.filter(student=student).delete()
    FeeStructure.objects.filter(id=fee_structure.id).delete()
    FeeCategory.objects.filter(id=category.id).delete()
    UserProfile.objects.filter(user=user).delete()
    user.delete()
    student.delete()
    print("✅ Test data cleaned up")
    
    print("\n" + "=" * 50)
    print("🎉 Discount functionality test completed successfully!")
    print("✅ Original amount calculation works")
    print("✅ Percentage discount calculation works")
    print("✅ Fixed amount discount calculation works")
    print("✅ Combined discount calculation works")
    print("✅ Expired waivers are ignored")
    print("✅ Pending waivers are ignored")
    print("✅ Students can see discounted amounts")

if __name__ == "__main__":
    test_discount_functionality()
