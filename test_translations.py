#!/usr/bin/env python
"""
Test if translations are working properly
"""
import os
import sys
import django

# Add the donation directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'donation'))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils.translation import activate, gettext as _
from django.conf import settings

def test_translations():
    """Test if translations are working"""
    print("Testing translations...")
    
    # Test English
    activate('en')
    print(f"\nEnglish (current): {settings.LANGUAGE_CODE}")
    print(f"English translation: {_('Charity Platform')}")
    print(f"English translation: {_('Make a Difference Today')}")
    
    # Test Malay
    activate('ms')
    print(f"\nMalay (current): {settings.LANGUAGE_CODE}")
    print(f"Malay translation: {_('Charity Platform')}")
    print(f"Malay translation: {_('Make a Difference Today')}")
    
    # Check if translation files exist
    print(f"\nLocale paths: {settings.LOCALE_PATHS}")
    print(f"Languages: {settings.LANGUAGES}")
    
    # Check if .mo files exist
    import os
    en_mo = os.path.join(settings.LOCALE_PATHS[0], 'en', 'LC_MESSAGES', 'django.mo')
    ms_mo = os.path.join(settings.LOCALE_PATHS[0], 'ms', 'LC_MESSAGES', 'django.mo')
    
    print(f"\nEnglish .mo file exists: {os.path.exists(en_mo)}")
    print(f"Malay .mo file exists: {os.path.exists(ms_mo)}")
    
    if not os.path.exists(en_mo) or not os.path.exists(ms_mo):
        print("\n❌ Translation files (.mo) are missing!")
        print("This is why language switching isn't working.")
        print("The .po files exist but need to be compiled to .mo files.")
    else:
        print("\n✅ Translation files (.mo) exist!")

if __name__ == '__main__':
    test_translations()
