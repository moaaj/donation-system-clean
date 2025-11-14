#!/usr/bin/env python
"""
Test anonymous user cart functionality
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
from myapp.models import DonationEvent

def test_cart_functionality():
    """Test anonymous user cart functionality"""
    
    print("🛒 TESTING ANONYMOUS CART FUNCTIONALITY")
    print("=" * 50)
    
    client = Client()
    
    # Get first donation event
    event = DonationEvent.objects.first()
    if not event:
        print("❌ No donation events found!")
        return
    
    print(f"Using event: {event.title} (ID: {event.id})")
    
    # Test 1: Add to cart
    print("\n1. Testing add to cart...")
    
    cart_data = {
        'amount': '50.00',
        'message': 'Test cart item from anonymous user',
        'donor_name': 'Test Anonymous Donor',
        'donor_email': 'test.anonymous@example.com'
    }
    
    response = client.post(f'/donation/cart/add/{event.id}/', cart_data, 
                          HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    print(f"Add to cart response status: {response.status_code}")
    print(f"Add to cart response content: {response.content.decode('utf-8')}")
    
    if response.status_code == 200:
        print("✅ Add to cart successful")
        
        # Check if item was added to session cart
        session = client.session
        if 'donation_cart' in session and len(session['donation_cart']) > 0:
            print("✅ Item added to session cart")
            print(f"Cart items: {session['donation_cart']}")
        else:
            print("❌ Item not found in session cart")
    else:
        print(f"❌ Add to cart failed (Status: {response.status_code})")
    
    # Test 2: View cart
    print("\n2. Testing view cart...")
    
    response = client.get('/donation/cart/')
    print(f"View cart response status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ View cart accessible")
    else:
        print(f"❌ View cart failed (Status: {response.status_code})")
    
    # Test 3: Cart count
    print("\n3. Testing cart count...")
    
    response = client.get('/donation/api/cart/count/')
    print(f"Cart count response status: {response.status_code}")
    print(f"Cart count response content: {response.content.decode('utf-8')}")
    
    if response.status_code == 200:
        print("✅ Cart count API working")
    else:
        print(f"❌ Cart count API failed (Status: {response.status_code})")
    
    print(f"\n📊 CART FUNCTIONALITY TEST COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    test_cart_functionality()
