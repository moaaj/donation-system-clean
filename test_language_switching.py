#!/usr/bin/env python
"""
Test script to verify language switching functionality
"""
import os
import sys
import django
from django.conf import settings

# Add the donation directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'donation'))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from django.utils.translation import activate

def test_language_switching():
    """Test that language switching works correctly"""
    client = Client()
    
    print("Testing language switching functionality...")
    
    # Test English (default)
    print("\n1. Testing English language:")
    response = client.get('/')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        if 'Charity Platform' in content:
            print("   ✓ English text found")
        else:
            print("   ✗ English text not found")
        
        # Check for toggle switch
        if 'languageToggle' in content and 'language-switch' in content:
            print("   ✓ Language toggle switch found")
        else:
            print("   ✗ Language toggle switch not found")
    
    # Test Malay language
    print("\n2. Testing Malay language:")
    response = client.get('/i18n/setlang/?language=ms')
    print(f"   Status: {response.status_code}")
    
    # Follow redirect and check content
    if response.status_code == 302:
        response = client.get(response.url)
        print(f"   Redirect status: {response.status_code}")
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            if 'Platform Amal' in content or 'Buat Perbezaan Hari Ini' in content:
                print("   ✓ Malay text found")
            else:
                print("   ✗ Malay text not found")
                print("   Content preview:", content[:200] + "...")
            
            # Check toggle state for Malay
            if 'checked' in content and 'languageToggle' in content:
                print("   ✓ Toggle switch state updated for Malay")
            else:
                print("   ✗ Toggle switch state not updated")
    
    # Test cart page with translations
    print("\n3. Testing cart page translations:")
    response = client.get('/donation/cart/')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        if 'Donation Cart' in content or 'Troli Derma' in content:
            print("   ✓ Cart page accessible")
        else:
            print("   ✗ Cart page issues")
    
    # Test toggle switch functionality
    print("\n4. Testing toggle switch elements:")
    response = client.get('/')
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        if 'EN' in content and 'MS' in content:
            print("   ✓ Language labels (EN/MS) found")
        else:
            print("   ✗ Language labels not found")
        
        if 'toggleLanguage()' in content:
            print("   ✓ Toggle function found")
        else:
            print("   ✗ Toggle function not found")
    
    print("\nLanguage toggle test completed!")

if __name__ == '__main__':
    test_language_switching()
