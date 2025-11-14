#!/usr/bin/env python
"""
Simple test to verify Django is working and language switcher is visible
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
from django.template.loader import render_to_string

def test_language_switcher():
    """Test if the language switcher is visible in the template"""
    print("Testing language switcher visibility...")
    
    try:
        # Test rendering the base template
        context = {
            'LANGUAGE_CODE': 'en',
        }
        
        # Try to render the base template
        html = render_to_string('base.html', context)
        
        # Check if language switcher elements are present
        if 'simple-language-switcher' in html:
            print("✅ Language switcher container found in template")
        else:
            print("❌ Language switcher container NOT found in template")
            
        if 'lang-btn' in html:
            print("✅ Language buttons found in template")
        else:
            print("❌ Language buttons NOT found in template")
            
        if 'English' in html and 'Malay' in html:
            print("✅ Language labels found in template")
        else:
            print("❌ Language labels NOT found in template")
            
        # Check for specific elements
        if 'simple-language-switcher' in html and 'lang-btn' in html:
            print("✅ Language switcher appears to be properly implemented")
            return True
        else:
            print("❌ Language switcher is missing or incomplete")
            return False
            
    except Exception as e:
        print(f"❌ Error testing language switcher: {e}")
        return False

def test_django_server():
    """Test if Django server can start"""
    print("\nTesting Django server...")
    
    try:
        client = Client()
        response = client.get('/')
        print(f"Home page status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            if 'simple-language-switcher' in content:
                print("✅ Language switcher found on home page")
                return True
            else:
                print("❌ Language switcher NOT found on home page")
                return False
        else:
            print(f"❌ Home page returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Django server: {e}")
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("LANGUAGE SWITCHER TEST")
    print("=" * 50)
    
    template_test = test_language_switcher()
    server_test = test_django_server()
    
    print("\n" + "=" * 50)
    print("RESULTS")
    print("=" * 50)
    
    if template_test and server_test:
        print("✅ All tests passed! Language switcher should be visible.")
    elif template_test:
        print("⚠️ Template test passed, but server test failed. Check Django server.")
    elif server_test:
        print("⚠️ Server test passed, but template test failed. Check template.")
    else:
        print("❌ Both tests failed. Check Django setup and template.")
    
    print("\nTo test manually:")
    print("1. Run: cd donation && python manage.py runserver")
    print("2. Open: http://127.0.0.1:8000/")
    print("3. Look for 'ENGLISH' and 'MALAY' buttons in the navigation bar")
