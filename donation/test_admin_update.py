#!/usr/bin/env python
"""
Test script to verify admin form updates work correctly
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from myapp.models import PibgDonationSettings
from myapp.admin import PibgDonationSettingsForm

def test_admin_form_update():
    """Test that admin form updates work correctly"""
    print("🔧 Testing Admin Form Updates")
    print("=" * 50)
    
    # Get current settings
    settings = PibgDonationSettings.get_settings()
    print(f"Current amounts: {settings.preset_amounts}")
    
    # Test 1: Simulate admin form submission
    print("\n1. Testing form submission simulation...")
    try:
        form_data = {
            'banner_text': settings.banner_text,
            'donation_message': settings.donation_message,
            'is_enabled': settings.is_enabled,
            'is_mandatory': settings.is_mandatory,
            'minimum_custom_amount': settings.minimum_custom_amount,
            'maximum_custom_amount': settings.maximum_custom_amount,
            # Test with new amounts
            'amount_1': 15.00,
            'amount_2': 25.00,
            'amount_3': 35.00,
            'amount_4': 75.00,
            'amount_5': 125.00,
            'amount_6': '',  # Empty
            'amount_7': '',  # Empty
            'amount_8': '',  # Empty
        }
        
        form = PibgDonationSettingsForm(data=form_data, instance=settings)
        if form.is_valid():
            print("   ✅ Form is valid")
            
            # Save the form
            updated_settings = form.save()
            
            # Check if amounts were updated
            expected_amounts = [15.0, 25.0, 35.0, 75.0, 125.0]
            if updated_settings.preset_amounts == expected_amounts:
                print(f"   ✅ Amounts updated correctly: {updated_settings.preset_amounts}")
            else:
                print(f"   ❌ Amounts not updated correctly. Expected: {expected_amounts}, Got: {updated_settings.preset_amounts}")
            
            # Verify in database
            updated_settings.refresh_from_db()
            if updated_settings.preset_amounts == expected_amounts:
                print("   ✅ Database updated correctly")
            else:
                print(f"   ❌ Database not updated. DB value: {updated_settings.preset_amounts}")
                
        else:
            print(f"   ❌ Form validation failed: {form.errors}")
            
    except Exception as e:
        print(f"   ❌ Error in form test: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Test with different amounts
    print("\n2. Testing with different amounts...")
    try:
        form_data_2 = {
            'banner_text': settings.banner_text,
            'donation_message': settings.donation_message,
            'is_enabled': settings.is_enabled,
            'is_mandatory': settings.is_mandatory,
            'minimum_custom_amount': settings.minimum_custom_amount,
            'maximum_custom_amount': settings.maximum_custom_amount,
            # Test with different amounts
            'amount_1': 5.00,
            'amount_2': 10.00,
            'amount_3': 20.00,
            'amount_4': '',  # Empty
            'amount_5': '',  # Empty
            'amount_6': '',  # Empty
            'amount_7': '',  # Empty
            'amount_8': '',  # Empty
        }
        
        form = PibgDonationSettingsForm(data=form_data_2, instance=settings)
        if form.is_valid():
            updated_settings = form.save()
            expected_amounts = [5.0, 10.0, 20.0]
            
            if updated_settings.preset_amounts == expected_amounts:
                print(f"   ✅ Second update successful: {updated_settings.preset_amounts}")
            else:
                print(f"   ❌ Second update failed. Expected: {expected_amounts}, Got: {updated_settings.preset_amounts}")
        else:
            print(f"   ❌ Second form validation failed: {form.errors}")
            
    except Exception as e:
        print(f"   ❌ Error in second test: {e}")
    
    # Test 3: Restore original amounts
    print("\n3. Restoring original amounts...")
    try:
        original_amounts = [10.0, 20.0, 30.0, 50.0, 100.0, 150.0, 200.0, 250.0]
        settings.preset_amounts = original_amounts
        settings.save()
        
        settings.refresh_from_db()
        if settings.preset_amounts == original_amounts:
            print(f"   ✅ Original amounts restored: {settings.preset_amounts}")
        else:
            print(f"   ❌ Failed to restore original amounts")
            
    except Exception as e:
        print(f"   ❌ Error restoring amounts: {e}")
    
    print("\n" + "=" * 50)
    print("🔧 Admin form update test completed!")
    print("\nIf all tests show ✅, the admin form should work correctly.")
    print("Try updating amounts in the admin interface now.")

if __name__ == '__main__':
    test_admin_form_update()
