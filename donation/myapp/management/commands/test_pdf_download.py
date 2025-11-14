from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from myapp.models import Student
from django.test import Client
from django.urls import reverse

class Command(BaseCommand):
    help = 'Test PDF download functionality for superuser'

    def handle(self, *args, **options):
        self.stdout.write("=== Testing PDF Download Functionality ===\n")
        
        # Check if moaaj user exists
        try:
            moaaj_user = User.objects.get(username='moaaj')
            self.stdout.write(f"✅ Found superuser: {moaaj_user.username}")
            self.stdout.write(f"   - Is superuser: {moaaj_user.is_superuser}")
            self.stdout.write(f"   - Is staff: {moaaj_user.is_staff}")
        except User.DoesNotExist:
            self.stdout.write("❌ Superuser 'moaaj' not found")
            return
        
        # Check total students
        total_students = Student.objects.count()
        self.stdout.write(f"✅ Total students in database: {total_students}")
        
        # Test PDF download URL
        client = Client()
        pdf_url = '/school-fees/students/download-pdf/'
        
        # Test without authentication (should redirect)
        self.stdout.write(f"\n--- Testing without authentication ---")
        response = client.get(pdf_url)
        self.stdout.write(f"Status code: {response.status_code}")
        if response.status_code == 302:
            self.stdout.write("✅ Correctly redirects unauthenticated users")
        else:
            self.stdout.write("❌ Should redirect unauthenticated users")
        
        # Test with authentication as superuser
        self.stdout.write(f"\n--- Testing with superuser authentication ---")
        client.force_login(moaaj_user)
        response = client.get(pdf_url)
        self.stdout.write(f"Status code: {response.status_code}")
        self.stdout.write(f"Content type: {response.get('Content-Type', 'Not set')}")
        self.stdout.write(f"Content disposition: {response.get('Content-Disposition', 'Not set')}")
        
        if response.status_code == 200:
            self.stdout.write("✅ PDF download successful")
            self.stdout.write(f"   - Response size: {len(response.content)} bytes")
            if 'application/pdf' in response.get('Content-Type', ''):
                self.stdout.write("✅ Correct content type (PDF)")
            else:
                self.stdout.write("❌ Incorrect content type")
        else:
            self.stdout.write("❌ PDF download failed")
        
        # Test with non-superuser
        self.stdout.write(f"\n--- Testing with non-superuser ---")
        try:
            regular_user = User.objects.filter(is_superuser=False).first()
            if regular_user:
                client.force_login(regular_user)
                response = client.get(pdf_url)
                self.stdout.write(f"Status code: {response.status_code}")
                if response.status_code == 302:
                    self.stdout.write("✅ Correctly redirects non-superusers")
                else:
                    self.stdout.write("❌ Should redirect non-superusers")
            else:
                self.stdout.write("⚠️ No regular users found to test with")
        except Exception as e:
            self.stdout.write(f"❌ Error testing non-superuser: {e}")
        
        self.stdout.write(f"\n=== Test Complete ===")
        self.stdout.write(f"PDF Download URL: {pdf_url}")
        self.stdout.write(f"Student List URL: /school-fees/students/")
