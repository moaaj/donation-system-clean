#!/usr/bin/env python
"""
Debug anonymous donation functionality
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
from myapp.models import DonationEvent, Donation

def test_donation_debug():
    """Debug anonymous donation functionality"""
    
    print("🔍 DEBUGGING ANONYMOUS DONATION")
    print("=" * 50)
    
    client = Client()
    
    # Test 1: Check if we have donation events
    print("\n1. Checking donation events...")
    events = DonationEvent.objects.all()
    print(f"Found {events.count()} donation events")
    
    if events.exists():
        event = events.first()
        print(f"First event: {event.title} (ID: {event.id})")
    else:
        print("❌ No donation events found!")
        return
    
    # Test 2: Test donation form submission
    print("\n2. Testing donation form submission...")
    
    donation_data = {
        'event': event.id,
        'donor_name': 'Test Anonymous Donor',
        'donor_email': 'test.anonymous@example.com',
        'amount': '25.00',
        'payment_method': 'paypal',
        'message': 'Test donation from anonymous user'
    }
    
    print(f"Sending POST to /donation/ with data: {donation_data}")
    
    response = client.post('/donation/', donation_data, 
                          HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    
    print(f"Response status: {response.status_code}")
    print(f"Response content: {response.content.decode('utf-8')}")
    
    # Test 3: Check if donation was created
    print("\n3. Checking if donation was created...")
    donation_count = Donation.objects.filter(donor_email='test.anonymous@example.com').count()
    print(f"Donations found: {donation_count}")
    
    if donation_count > 0:
        donation = Donation.objects.filter(donor_email='test.anonymous@example.com').first()
        print(f"Donation details: {donation.donor_name} - ${donation.amount}")
    else:
        print("❌ No donation was created!")
    
    # Test 4: Test regular form submission (not AJAX)
    print("\n4. Testing regular form submission...")
    
    response2 = client.post('/donation/', donation_data)
    print(f"Regular POST response status: {response2.status_code}")
    
    if response2.status_code == 302:
        print("✅ Regular POST redirected (expected)")
    else:
        print(f"❌ Regular POST unexpected status: {response2.status_code}")
        print(f"Response content: {response2.content.decode('utf-8')[:500]}...")

if __name__ == "__main__":
    test_donation_debug()
