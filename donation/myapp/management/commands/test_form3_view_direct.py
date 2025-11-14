from django.core.management.base import BaseCommand
from django.test import RequestFactory, Client
from django.contrib.auth.models import User
from myapp.views_ubac import form3_admin_dashboard, form3_students_page
from myapp.models import UserProfile

class Command(BaseCommand):
    help = 'Test Form 3 views directly'

    def handle(self, *args, **options):
        self.stdout.write("=== Testing Form 3 Views Directly ===\n")
        
        # Create a test client
        client = Client()
        
        # Get the form3_admin user
        try:
            user = User.objects.get(username='form3_admin')
            self.stdout.write(f"✅ Found user: {user.username}")
        except User.DoesNotExist:
            self.stdout.write("❌ form3_admin user not found")
            return
        
        # Login the user
        login_success = client.login(username='form3_admin', password='form3admin123')
        if not login_success:
            self.stdout.write("❌ Login failed")
            return
        
        self.stdout.write("✅ Login successful")
        
        # Test dashboard view
        self.stdout.write("\n1. Testing dashboard view...")
        try:
            response = client.get('/form3-admin/')
            self.stdout.write(f"   Status: {response.status_code}")
            if response.status_code == 200:
                context = response.context
                if context:
                    self.stdout.write(f"   Total students: {context.get('total_form3_students', 'NOT FOUND')}")
                    self.stdout.write(f"   Total payments: {context.get('total_form3_payments', 'NOT FOUND')}")
                    self.stdout.write(f"   Total revenue: {context.get('total_form3_revenue', 'NOT FOUND')}")
                else:
                    self.stdout.write("   ❌ No context data available")
                
                # Check if the response contains the right data
                content = response.content.decode('utf-8')
                if '91' in content:
                    self.stdout.write("   ✅ Response contains '91' (correct student count)")
                else:
                    self.stdout.write("   ❌ Response does not contain '91'")
                    # Show a snippet of the content
                    self.stdout.write(f"   Content snippet: {content[:200]}...")
            else:
                self.stdout.write(f"   ❌ Dashboard view failed with status {response.status_code}")
        except Exception as e:
            self.stdout.write(f"   ❌ Dashboard view error: {e}")
        
        # Test students page view
        self.stdout.write("\n2. Testing students page view...")
        try:
            response = client.get('/form3-admin/students/')
            self.stdout.write(f"   Status: {response.status_code}")
            if response.status_code == 200:
                context = response.context
                students = context.get('students', None)
                if students:
                    self.stdout.write(f"   Total students: {students.paginator.count}")
                    self.stdout.write(f"   Students on page: {len(students)}")
                    self.stdout.write(f"   Current page: {students.number} of {students.paginator.num_pages}")
                else:
                    self.stdout.write("   ❌ No students object in context")
                
                # Check if the response contains the right data
                content = response.content.decode('utf-8')
                if '91' in content:
                    self.stdout.write("   ✅ Response contains '91' (correct student count)")
                else:
                    self.stdout.write("   ❌ Response does not contain '91'")
                    # Show a snippet of the content
                    self.stdout.write(f"   Content snippet: {content[:200]}...")
            else:
                self.stdout.write(f"   ❌ Students page view failed with status {response.status_code}")
        except Exception as e:
            self.stdout.write(f"   ❌ Students page view error: {e}")
        
        self.stdout.write("\n=== Test Complete ===")
