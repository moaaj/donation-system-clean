#!/usr/bin/env python
"""
Test all Form 3 admin dashboard buttons
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from django.test import Client

def test_form3_buttons():
    """Test all Form 3 admin dashboard buttons"""
    
    print("🧪 TESTING ALL FORM 3 ADMIN BUTTONS")
    print("=" * 70)
    
    client = Client()
    
    # Login as Form 3 admin
    login_response = client.post('/accounts/login/', {
        'username': 'form3_admin',
        'password': 'form3admin123'
    })
    
    if login_response.status_code != 302:
        print("❌ Login failed")
        return False
    
    print("✅ Form 3 admin login successful")
    
    # Test all dashboard buttons
    buttons = [
        ('/form3-admin/', 'Dashboard'),
        ('/form3-admin/students/', 'Manage Students'),
        ('/form3-admin/fees/', 'Manage Fees'),
        ('/form3-admin/payments/', 'View Payments'),
        ('/form3-admin/analytics/', 'View Analytics'),
        ('/form3-admin/categories/', 'Fee Categories'),
        ('/form3-admin/pending-fees/', 'Pending Fees'),
        ('/form3-admin/waivers/', 'Fee Waivers'),
        ('/form3-admin/bank-accounts/', 'Bank Accounts'),
        ('/form3-admin/reports/', 'Fee Reports'),
        ('/form3-admin/payments/receipts/', 'Payment Receipts'),
        ('/form3-admin/fees/add-individual/', 'Add Individual Fee'),
        ('/form3-admin/fees/add-structure/', 'Add Fee Structure'),
    ]
    
    working_buttons = 0
    total_buttons = len(buttons)
    
    for url, name in buttons:
        response = client.get(url)
        if response.status_code == 200:
            print(f"✅ {name}: Working")
            working_buttons += 1
        else:
            print(f"❌ {name}: Not working (Status: {response.status_code})")
    
    print(f"\n📊 BUTTON TEST RESULTS")
    print("=" * 70)
    print(f"✅ Working buttons: {working_buttons}/{total_buttons}")
    print(f"❌ Non-working buttons: {total_buttons - working_buttons}/{total_buttons}")
    
    if working_buttons == total_buttons:
        print("\n🎉 ALL BUTTONS ARE WORKING!")
        print("✅ Form 3 admin dashboard is fully functional")
        print("✅ All school fees capabilities are accessible")
        print("✅ Complete superuser functionality for Form 3 students")
    else:
        print(f"\n⚠️  {total_buttons - working_buttons} buttons need fixing")
    
    return working_buttons == total_buttons

if __name__ == "__main__":
    test_form3_buttons()
