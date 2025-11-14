#!/usr/bin/env python
"""
Script to create test user activities for demonstration
"""

import os
import sys
import django
from datetime import datetime, timedelta
import random

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from accounts.models import UserActivity, LoginAttempt
from django.contrib.auth.models import User
from django.utils import timezone

def create_test_activities():
    """Create test user activities for demonstration"""
    
    print("🎯 CREATING TEST USER ACTIVITIES")
    print("=" * 60)
    
    # Get or create test users
    users = []
    
    # Check if tamim123 exists
    try:
        tamim123 = User.objects.get(username='tamim123')
        users.append(tamim123)
        print(f"✅ Found existing user: {tamim123.username}")
    except User.DoesNotExist:
        # Create tamim123 if it doesn't exist
        tamim123 = User.objects.create_user(
            username='tamim123',
            email='tamim123@example.com',
            password='testpass123',
            first_name='Tamim',
            last_name='Student'
        )
        users.append(tamim123)
        print(f"✅ Created user: {tamim123.username}")
    
    # Get other existing users
    existing_users = User.objects.exclude(username='tamim123')[:5]
    users.extend(existing_users)
    
    print(f"📊 Total users for activity generation: {len(users)}")
    
    # Create activities for the last 7 days
    now = timezone.now()
    activities_created = 0
    
    for user in users:
        print(f"\n👤 Creating activities for: {user.username}")
        
        # Create 2-5 login/logout pairs per day for the last 7 days
        for day_offset in range(7):
            date = now.date() - timedelta(days=day_offset)
            
            # Create 2-5 sessions per day
            sessions_per_day = random.randint(2, 5)
            
            for session in range(sessions_per_day):
                # Random time during the day
                hour = random.randint(8, 22)  # Between 8 AM and 10 PM
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                
                login_time = datetime.combine(date, datetime.min.time().replace(hour=hour, minute=minute, second=second))
                login_time = timezone.make_aware(login_time)
                
                # Logout time (15 minutes to 2 hours later)
                session_duration = timedelta(minutes=random.randint(15, 120))
                logout_time = login_time + session_duration
                
                # Create login activity
                login_activity = UserActivity.objects.create(
                    user=user,
                    activity_type='login',
                    ip_address=f"192.168.1.{random.randint(1, 255)}",
                    user_agent=f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(90, 120)}.0.0.0 Safari/537.36",
                    timestamp=login_time
                )
                activities_created += 1
                
                # Create logout activity
                logout_activity = UserActivity.objects.create(
                    user=user,
                    activity_type='logout',
                    ip_address=login_activity.ip_address,  # Same IP for session
                    user_agent=login_activity.user_agent,  # Same user agent for session
                    timestamp=logout_time
                )
                activities_created += 1
                
                print(f"   📅 {date.strftime('%Y-%m-%d')} - Session {session+1}: Login at {login_time.strftime('%H:%M:%S')}, Logout at {logout_time.strftime('%H:%M:%S')}")
    
    # Create some failed login attempts
    failed_attempts = 0
    for user in users:
        # Create 1-3 failed attempts per user
        for attempt in range(random.randint(1, 3)):
            attempt_time = now - timedelta(hours=random.randint(1, 168))  # Last week
            LoginAttempt.objects.create(
                user=None,  # Failed attempts don't have a user
                ip_address=f"192.168.1.{random.randint(1, 255)}",
                user_agent=f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(90, 120)}.0.0.0 Safari/537.36",
                timestamp=attempt_time,
                success=False
            )
            failed_attempts += 1
    
    # Create some successful login attempts
    successful_attempts = 0
    for user in users:
        # Create 1-2 successful attempts per user
        for attempt in range(random.randint(1, 2)):
            attempt_time = now - timedelta(hours=random.randint(1, 168))  # Last week
            LoginAttempt.objects.create(
                user=user,
                ip_address=f"192.168.1.{random.randint(1, 255)}",
                user_agent=f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(90, 120)}.0.0.0 Safari/537.36",
                timestamp=attempt_time,
                success=True
            )
            successful_attempts += 1
    
    print(f"\n" + "=" * 60)
    print(f"✅ ACTIVITY GENERATION COMPLETE!")
    print(f"📊 Total activities created: {activities_created}")
    print(f"🚨 Failed login attempts: {failed_attempts}")
    print(f"✅ Successful login attempts: {successful_attempts}")
    print(f"👥 Users with activities: {len(users)}")
    
    # Show summary by user
    print(f"\n📋 ACTIVITY SUMMARY BY USER:")
    for user in users:
        user_activities = UserActivity.objects.filter(user=user).count()
        user_logins = UserActivity.objects.filter(user=user, activity_type='login').count()
        user_logouts = UserActivity.objects.filter(user=user, activity_type='logout').count()
        print(f"   {user.username}: {user_activities} activities ({user_logins} logins, {user_logouts} logouts)")
    
    print(f"\n🚀 NEXT STEPS:")
    print(f"1. Run the server: python manage.py runserver")
    print(f"2. Login as superuser")
    print(f"3. Go to: http://127.0.0.1:8000/admin/")
    print(f"4. View the dashboard with all activities")
    print(f"5. Check user activity tracking for tamim123 and others")
    
    print(f"\n" + "=" * 60)

if __name__ == "__main__":
    create_test_activities()
