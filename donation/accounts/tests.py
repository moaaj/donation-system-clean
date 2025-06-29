from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .forms import RoleBasedRegistrationForm
from myapp.models import Student, UserProfile as MyAppUserProfile


class RoleBasedRegistrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('accounts:register')

    def test_admin_registration_with_valid_email(self):
        """Test admin registration with @admin.com email"""
        form_data = {
            'username': 'adminuser',
            'email': 'admin@admin.com',
            'first_name': 'Admin',
            'last_name': 'User',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'role': 'admin',
            'phone_number': '1234567890',
            'address': 'Admin Address'
        }
        
        form = RoleBasedRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Test the view
        response = self.client.post(self.register_url, form_data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Check if user was created
        user = User.objects.get(username='adminuser')
        self.assertEqual(user.email, 'admin@admin.com')
        self.assertTrue(user.is_staff)
        
        # Check if profile was created
        profile = MyAppUserProfile.objects.get(user=user)
        self.assertEqual(profile.role, 'admin')

    def test_admin_registration_with_invalid_email(self):
        """Test admin registration with non-admin email should fail"""
        form_data = {
            'username': 'adminuser',
            'email': 'admin@gmail.com',  # Not @admin.com
            'first_name': 'Admin',
            'last_name': 'User',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'role': 'admin',
            'phone_number': '1234567890',
            'address': 'Admin Address'
        }
        
        form = RoleBasedRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Admin email addresses must end with @admin.com', str(form.errors['email']))

    def test_student_registration_with_student_id(self):
        """Test student registration with valid student ID"""
        form_data = {
            'username': 'studentuser',
            'email': 'student@gmail.com',
            'first_name': 'Student',
            'last_name': 'User',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'role': 'student',
            'student_id': 'STU2024001',
            'phone_number': '1234567890',
            'address': 'Student Address'
        }
        
        form = RoleBasedRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Test the view
        response = self.client.post(self.register_url, form_data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Check if user was created
        user = User.objects.get(username='studentuser')
        self.assertEqual(user.email, 'student@gmail.com')
        self.assertFalse(user.is_staff)
        
        # Check if profile was created
        profile = MyAppUserProfile.objects.get(user=user)
        self.assertEqual(profile.role, 'student')
        
        # Check if student record was created
        student = Student.objects.get(student_id='STU2024001')
        self.assertEqual(student.first_name, 'Student')
        self.assertEqual(student.last_name, 'User')

    def test_student_registration_without_student_id(self):
        """Test student registration without student ID should fail"""
        form_data = {
            'username': 'studentuser',
            'email': 'student@gmail.com',
            'first_name': 'Student',
            'last_name': 'User',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'role': 'student',
            'student_id': '',  # Empty student ID
            'phone_number': '1234567890',
            'address': 'Student Address'
        }
        
        form = RoleBasedRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Student ID is required for student registration', str(form.errors['student_id']))

    def test_student_registration_with_duplicate_student_id(self):
        """Test student registration with duplicate student ID should fail"""
        # Create a student first
        student = Student.objects.create(
            student_id='STU2024001',
            first_name='Existing',
            last_name='Student',
            year_batch=2024,
            nric='123456789012'
        )
        
        form_data = {
            'username': 'studentuser',
            'email': 'student@gmail.com',
            'first_name': 'Student',
            'last_name': 'User',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'role': 'student',
            'student_id': 'STU2024001',  # Duplicate student ID
            'phone_number': '1234567890',
            'address': 'Student Address'
        }
        
        form = RoleBasedRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('This student ID is already registered', str(form.errors['student_id']))

    def test_registration_form_rendering(self):
        """Test that the registration form renders correctly"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Account')
        self.assertContains(response, 'Role')
        self.assertContains(response, 'Admin')
        self.assertContains(response, 'Student') 