#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from django.conf import settings
from django.db import connection

def show_database_info():
    """Show database connection information"""
    print("🔍 Database Connection Information")
    print("=" * 50)
    
    # Show Django database settings
    db_settings = settings.DATABASES['default']
    print(f"Database Engine: {db_settings['ENGINE']}")
    print(f"Database Name: {db_settings['NAME']}")
    print(f"Database Host: {db_settings['HOST']}")
    print(f"Database Port: {db_settings['PORT']}")
    print(f"Database User: {db_settings['USER']}")
    
    # Test connection and get actual database info
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database(), current_user, version();")
            db_name, db_user, db_version = cursor.fetchone()
            print(f"\n✅ Active Connection:")
            print(f"   - Database: {db_name}")
            print(f"   - User: {db_user}")
            print(f"   - Version: {db_version}")
            
            # Check if auth_user table exists and count users
            cursor.execute("SELECT COUNT(*) FROM auth_user;")
            user_count = cursor.fetchone()[0]
            print(f"   - Users in auth_user table: {user_count}")
            
            # Show recent users
            cursor.execute("""
                SELECT id, username, email, first_name, last_name, is_staff, date_joined 
                FROM auth_user 
                ORDER BY date_joined DESC 
                LIMIT 5;
            """)
            recent_users = cursor.fetchall()
            print(f"\n📋 Recent users in auth_user table:")
            for user in recent_users:
                print(f"   - ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Created: {user[6]}")
                
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")

if __name__ == "__main__":
    show_database_info() 