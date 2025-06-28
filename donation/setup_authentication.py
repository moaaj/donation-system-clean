#!/usr/bin/env python
"""
Setup script for enhanced authentication system with PostgreSQL optimization
for handling 1000+ users.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line
from django.db import connection

def setup_django():
    """Setup Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
    django.setup()

def create_superuser():
    """Create a superuser account"""
    from django.contrib.auth.models import User
    
    if User.objects.filter(is_superuser=True).exists():
        print("Superuser already exists.")
        return
    
    print("Creating superuser account...")
    username = input("Enter username for superuser: ")
    email = input("Enter email for superuser: ")
    password = input("Enter password for superuser: ")
    
    try:
        user = User.objects.create_superuser(username, email, password)
        print(f"Superuser '{username}' created successfully!")
    except Exception as e:
        print(f"Error creating superuser: {e}")

def optimize_database():
    """Apply database optimizations"""
    print("Applying database optimizations...")
    
    with connection.cursor() as cursor:
        # Create indexes for better performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_auth_user_username ON auth_user(username);",
            "CREATE INDEX IF NOT EXISTS idx_auth_user_email ON auth_user(email);",
            "CREATE INDEX IF NOT EXISTS idx_auth_user_is_active ON auth_user(is_active);",
            "CREATE INDEX IF NOT EXISTS idx_accounts_userprofile_user ON accounts_userprofile(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_accounts_userprofile_verified ON accounts_userprofile(is_verified);",
            "CREATE INDEX IF NOT EXISTS idx_accounts_loginattempt_user ON accounts_loginattempt(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_accounts_loginattempt_ip ON accounts_loginattempt(ip_address);",
            "CREATE INDEX IF NOT EXISTS idx_accounts_loginattempt_timestamp ON accounts_loginattempt(timestamp);",
            "CREATE INDEX IF NOT EXISTS idx_accounts_loginattempt_success ON accounts_loginattempt(success);",
        ]
        
        for index in indexes:
            try:
                cursor.execute(index)
                print(f"Created index: {index.split('ON')[1].strip()}")
            except Exception as e:
                print(f"Error creating index: {e}")

def create_sample_users():
    """Create sample users for testing"""
    from django.contrib.auth.models import User
    from accounts.models import UserProfile
    
    print("Creating sample users...")
    
    sample_users = [
        {
            'username': 'testuser1',
            'email': 'test1@example.com',
            'first_name': 'Test',
            'last_name': 'User1',
            'password': 'testpass123'
        },
        {
            'username': 'testuser2',
            'email': 'test2@example.com',
            'first_name': 'Test',
            'last_name': 'User2',
            'password': 'testpass123'
        },
        {
            'username': 'admin_user',
            'email': 'admin@example.com',
            'first_name': 'Admin',
            'last_name': 'User',
            'password': 'adminpass123'
        }
    ]
    
    for user_data in sample_users:
        if not User.objects.filter(username=user_data['username']).exists():
            try:
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    password=user_data['password']
                )
                print(f"Created user: {user.username}")
            except Exception as e:
                print(f"Error creating user {user_data['username']}: {e}")

def check_database_connection():
    """Check database connection"""
    print("Checking database connection...")
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"Database connected successfully!")
            print(f"PostgreSQL version: {version[0]}")
            return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

def run_migrations():
    """Run Django migrations"""
    print("Running migrations...")
    try:
        execute_from_command_line(['manage.py', 'makemigrations'])
        execute_from_command_line(['manage.py', 'migrate'])
        print("Migrations completed successfully!")
    except Exception as e:
        print(f"Error running migrations: {e}")

def main():
    """Main setup function"""
    print("=" * 50)
    print("Enhanced Authentication System Setup")
    print("Optimized for 1000+ Users with PostgreSQL")
    print("=" * 50)
    
    # Setup Django
    setup_django()
    
    # Check database connection
    if not check_database_connection():
        print("Please check your database configuration and try again.")
        return
    
    # Run migrations
    run_migrations()
    
    # Apply database optimizations
    optimize_database()
    
    # Create superuser
    create_superuser()
    
    # Create sample users
    create_sample_users()
    
    print("\n" + "=" * 50)
    print("Setup completed successfully!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Start the development server: python manage.py runserver")
    print("2. Visit http://127.0.0.1:8000/accounts/login/ to test login")
    print("3. Visit http://127.0.0.1:8000/accounts/register/ to test registration")
    print("4. Visit http://127.0.0.1:8000/admin/ to access admin panel")
    print("\nFor production deployment:")
    print("1. Set DEBUG = False in settings.py")
    print("2. Configure proper email settings")
    print("3. Set up SSL/HTTPS")
    print("4. Configure PostgreSQL for production")
    print("5. Set up Redis for caching (optional)")

if __name__ == '__main__':
    main() 