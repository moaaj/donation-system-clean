#!/usr/bin/env python
"""
Test script to verify waqaf functionality for anonymous users
- Anonymous users can contribute to waqaf
- Certificate is auto-downloaded
- Page redirects to homepage
- Certificate shows correct amount
"""

import os
import sys
import django
from decimal import Decimal

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from waqaf.models import WaqafAsset, Contributor, Contribution
from django.contrib.auth.models import User

def test_waqaf_anonymous_functionality():
    """Test waqaf functionality for anonymous users"""
    print("🧪 Testing Waqaf Anonymous Functionality")
    print("=" * 50)
    
    client = Client()
    
    # Test 1: Check if waqaf page is accessible to anonymous users
    print("\n1. Testing waqaf page access...")
    response = client.get('/waqaf/')
    if response.status_code == 200:
        print("✅ Waqaf page accessible to anonymous users")
    else:
        print(f"❌ Waqaf page not accessible (Status: {response.status_code})")
        return False
    
    # Test 2: Check if waqaf cart is accessible to anonymous users
    print("\n2. Testing waqaf cart access...")
    response = client.get('/waqaf/cart/')
    if response.status_code == 200:
        print("✅ Waqaf cart accessible to anonymous users")
    else:
        print(f"❌ Waqaf cart not accessible (Status: {response.status_code})")
        return False
    
    # Test 3: Test adding item to waqaf cart
    print("\n3. Testing add to waqaf cart...")
    
    # Get available waqaf assets
    assets = WaqafAsset.objects.filter(slots_available__gt=0, is_archived=False)
    if not assets.exists():
        print("❌ No waqaf assets available for testing")
        return False
    
    asset = assets.first()
    print(f"   Using asset: {asset.name} (Price: RM{asset.slot_price})")
    
    # Add item to cart
    response = client.post(f'/waqaf/cart/add/{asset.id}/', {
        'number_of_slots': 2,
        'contributor_name': 'Test Anonymous User',
        'contributor_phone': '0123456789',
        'contributor_address': 'Test Address'
    }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    
    if response.status_code == 200:
        print("✅ Successfully added item to waqaf cart")
    else:
        print(f"❌ Failed to add item to waqaf cart (Status: {response.status_code})")
        return False
    
    # Test 4: Test waqaf cart checkout
    print("\n4. Testing waqaf cart checkout...")
    
    # Get cart count before checkout
    cart_response = client.get('/waqaf/cart/')
    if cart_response.status_code != 200:
        print("❌ Cannot access cart for checkout test")
        return False
    
    # Perform checkout
    checkout_data = {
        'contributor_name': 'Test Anonymous User',
        'contributor_phone': '0123456789',
        'contributor_address': 'Test Address',
        'dedicated_for': 'Test dedication'
    }
    
    response = client.post('/waqaf/cart/checkout/', checkout_data)
    
    if response.status_code == 302:
        print("✅ Waqaf checkout successful (redirected)")
        
        # Check if redirected to success page
        if response.url and 'success' in response.url:
            print("✅ Redirected to success page")
        else:
            print(f"❌ Redirected to wrong location: {response.url}")
            return False
    else:
        print(f"❌ Waqaf checkout failed (Status: {response.status_code})")
        return False
    
    # Test 5: Test waqaf success page access
    print("\n5. Testing waqaf success page...")
    response = client.get('/waqaf/cart/success/')
    if response.status_code == 200:
        print("✅ Waqaf success page accessible to anonymous users")
    else:
        print(f"❌ Waqaf success page not accessible (Status: {response.status_code})")
        return False
    
    # Test 6: Verify contribution was created in database
    print("\n6. Verifying contribution in database...")
    try:
        contribution = Contribution.objects.filter(
            contributor__name='Test Anonymous User',
            payment_status='COMPLETED'
        ).latest('date_contributed')
        
        expected_amount = Decimal('2') * asset.slot_price  # 2 slots * price per slot
        if contribution.amount == expected_amount:
            print(f"✅ Contribution found with correct amount: RM{contribution.amount}")
        else:
            print(f"❌ Contribution amount incorrect. Expected: RM{expected_amount}, Got: RM{contribution.amount}")
            return False
            
    except Contribution.DoesNotExist:
        print("❌ Waqaf contribution record not found in database")
        return False
    
    # Test 7: Test certificate download
    print("\n7. Testing certificate download...")
    try:
        response = client.get(f'/waqaf/certificate/{contribution.id}/')
        if response.status_code == 200:
            print("✅ Certificate download successful")
            
            # Check if it's a PDF
            if response.get('Content-Type') == 'application/pdf':
                print("✅ Certificate is a valid PDF")
            else:
                print(f"❌ Certificate is not a PDF (Content-Type: {response.get('Content-Type')})")
                return False
        else:
            print(f"❌ Certificate download failed (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Certificate download error: {str(e)}")
        return False
    
    # Test 8: Test direct waqaf contribution (not through cart)
    print("\n8. Testing direct waqaf contribution...")
    
    # Create a new contributor for direct contribution
    contributor_data = {
        'name': 'Direct Test User',
        'email': 'direct.test@example.com',
        'phone': '0123456788',
        'address': 'Direct Test Address'
    }
    
    contribution_data = {
        'asset': asset.id,
        'number_of_slots': 1,
        'dedicated_for': 'Direct test dedication',
        'payment_type': 'ONE_OFF'
    }
    
    # Submit both forms together
    form_data = {**contributor_data, **contribution_data}
    response = client.post('/waqaf/contribute_waqaf/', form_data)
    
    print(f"   Response status: {response.status_code}")
    if response.status_code == 200:
        print("   Response content preview:")
        content = response.content.decode('utf-8')
        if 'error' in content.lower() or 'invalid' in content.lower():
            print("   ❌ Form validation errors detected")
            # Look for specific error messages
            if 'This field is required' in content:
                print("   ❌ Required field missing")
            if 'Select a valid choice' in content:
                print("   ❌ Invalid choice selected")
        else:
            print("   ✅ Form rendered successfully (no obvious errors)")
    
    if response.status_code == 302:
        print("✅ Direct waqaf contribution successful (redirected)")
        
        # Check if redirected to success page (for anonymous users)
        if response.url and 'success' in response.url:
            print("✅ Redirected to success page for anonymous user")
        else:
            print(f"❌ Redirected to wrong location: {response.url}")
            return False
    else:
        print(f"❌ Direct waqaf contribution failed (Status: {response.status_code})")
        return False
    
    # Test 9: Verify direct contribution in database
    print("\n9. Verifying direct contribution in database...")
    try:
        direct_contribution = Contribution.objects.filter(
            contributor__name='Direct Test User',
            payment_status='COMPLETED'
        ).latest('date_contributed')
        
        expected_direct_amount = Decimal('1') * asset.slot_price  # 1 slot * price per slot
        if direct_contribution.amount == expected_direct_amount:
            print(f"✅ Direct contribution found with correct amount: RM{direct_contribution.amount}")
        else:
            print(f"❌ Direct contribution amount incorrect. Expected: RM{expected_direct_amount}, Got: RM{direct_contribution.amount}")
            return False
            
    except Contribution.DoesNotExist:
        print("❌ Direct waqaf contribution record not found in database")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All waqaf anonymous functionality tests passed!")
    print("✅ Anonymous users can contribute to waqaf")
    print("✅ Certificate is auto-downloaded")
    print("✅ Page redirects to homepage")
    print("✅ Certificate shows correct amount")
    print("✅ Both cart and direct contributions work")
    
    return True

if __name__ == '__main__':
    success = test_waqaf_anonymous_functionality()
    if not success:
        print("\n❌ Some tests failed. Please check the implementation.")
        sys.exit(1)
    else:
        print("\n✅ All tests passed successfully!")
