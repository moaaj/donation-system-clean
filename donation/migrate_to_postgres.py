#!/usr/bin/env python
"""
Migration script to help move from SQLite to PostgreSQL
Run this script after setting up PostgreSQL and updating settings.py
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def main():
    # Add the project directory to Python path
    project_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_dir)
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
    django.setup()
    
    print("=== Django PostgreSQL Migration Script ===")
    print("This script will help you migrate from SQLite to PostgreSQL")
    print()
    
    # Check if we can connect to PostgreSQL
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"✅ Successfully connected to PostgreSQL: {version[0]}")
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        print("Please check your database settings and ensure PostgreSQL is running")
        return
    
    print("\n=== Running Django Commands ===")
    
    # Run migrations
    print("1. Running migrations...")
    execute_from_command_line(['manage.py', 'migrate'])
    
    # Create superuser if needed
    print("\n2. Creating superuser...")
    print("You'll be prompted to create a superuser account")
    execute_from_command_line(['manage.py', 'createsuperuser'])
    
    # Collect static files
    print("\n3. Collecting static files...")
    execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
    
    print("\n=== Migration Complete ===")
    print("Your Django app is now running on PostgreSQL!")
    print("You can start the development server with: python manage.py runserver")

if __name__ == '__main__':
    main() 