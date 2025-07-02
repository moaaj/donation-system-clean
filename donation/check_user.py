#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from django.contrib.auth.models import User
from django.db import connection

def check_user_in_database():
    """Check if mominul123 user exists in the database"""
    print("🔍 Checking for mominul123 user in database...")
    print("=" * 50)
    
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database();")
            db_name = cursor.fetchone()[0]
            print(f"✅ Connected to database: {db_name}")
        
        # Check total users
        total_users = User.objects.count()
        print(f"📊 Total users in database: {total_users}")
        
        # Check for mominul123 specifically
        try:
            user = User.objects.get(username='mominul123')
            print(f"✅ User 'mominul123' found!")
            print(f"   - ID: {user.id}")
            print(f"   - Email: {user.email}")
            print(f"   - First Name: {user.first_name}")
            print(f"   - Last Name: {user.last_name}")
            print(f"   - Is Staff: {user.is_staff}")
            print(f"   - Is Superuser: {user.is_superuser}")
            print(f"   - Date Joined: {user.date_joined}")
            print(f"   - Last Login: {user.last_login}")
            
            # Check if user has profiles
            try:
                profile = user.profile
                print(f"   - Has UserProfile: ✅")
                print(f"     - Phone: {profile.phone_number}")
                print(f"     - Address: {profile.address}")
            except:
                print(f"   - Has UserProfile: ❌")
            
            try:
                myapp_profile = user.myapp_profile
                print(f"   - Has MyAppUserProfile: ✅")
                print(f"     - Role: {myapp_profile.role}")
                print(f"     - Phone: {myapp_profile.phone_number}")
            except:
                print(f"   - Has MyAppUserProfile: ❌")
                
        except User.DoesNotExist:
            print("❌ User 'mominul123' NOT found in database")
            
            # Show recent users
            recent_users = User.objects.all().order_by('-date_joined')[:5]
            print(f"\n📋 Recent users in database:")
            for u in recent_users:
                print(f"   - {u.username} (ID: {u.id}, Email: {u.email}, Created: {u.date_joined})")
        
        # Check if there are any users with similar names
        similar_users = User.objects.filter(username__icontains='mominul')
        if similar_users.exists():
            print(f"\n🔍 Found users with similar names:")
            for u in similar_users:
                print(f"   - {u.username} (ID: {u.id}, Email: {u.email})")
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_user_in_database() 