#!/usr/bin/env python
"""
Simple test to check if language switching is working
"""
import os
import sys
import django

# Add the donation directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'donation'))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.utils.translation import activate

def test_language_switching():
    """Test language switching functionality"""
    print("Testing language switching...")
    
    client = Client()
    
    # Test English
    print("\n1. Testing English language:")
    response = client.get('/')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        if 'Charity Platform' in content:
            print("   ✅ English content found")
        else:
            print("   ❌ English content not found")
    
    # Test Malay language switching
    print("\n2. Testing Malay language switching:")
    response = client.get('/i18n/setlang/?language=ms')
    print(f"   Language switch status: {response.status_code}")
    
    if response.status_code == 302:  # Redirect response
        print("   ✅ Language switch redirect received")
        
        # Follow the redirect
        response = client.get(response.url)
        print(f"   Redirect follow status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            if 'Platform Amal' in content or 'Buat Perbezaan Hari Ini' in content:
                print("   ✅ Malay content found")
            else:
                print("   ❌ Malay content not found")
                print("   Content preview:", content[:200] + "...")
        else:
            print(f"   ❌ Redirect follow failed with status {response.status_code}")
    else:
        print(f"   ❌ Language switch failed with status {response.status_code}")
    
    # Test direct language activation
    print("\n3. Testing direct language activation:")
    try:
        activate('ms')
        print("   ✅ Malay language activated successfully")
        
        # Test if we can get Malay content
        response = client.get('/')
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            if 'Platform Amal' in content or 'Buat Perbezaan Hari Ini' in content:
                print("   ✅ Malay content found after activation")
            else:
                print("   ❌ Malay content not found after activation")
        else:
            print(f"   ❌ Request failed with status {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error activating Malay language: {e}")
    
    print("\n" + "="*50)
    print("LANGUAGE SWITCHING TEST COMPLETE")
    print("="*50)

if __name__ == '__main__':
    test_language_switching()
