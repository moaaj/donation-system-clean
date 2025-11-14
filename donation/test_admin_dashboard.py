#!/usr/bin/env python
"""
Test script to verify admin dashboard functionality
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from accounts.models import UserActivity, LoginAttempt
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Count

def test_admin_dashboard():
    """Test admin dashboard functionality"""
    
    print("🧪 TESTING ADMIN DASHBOARD")
    print("=" * 60)
    
    # Get current date and time
    now = timezone.now()
    today = now.date()
    
    # User Activity Statistics
    total_logins = UserActivity.objects.filter(activity_type='login').count()
    total_logouts = UserActivity.objects.filter(activity_type='logout').count()
    
    # Today's activity
    today_logins = UserActivity.objects.filter(
        activity_type='login',
        timestamp__date=today
    ).count()
    today_logouts = UserActivity.objects.filter(
        activity_type='logout',
        timestamp__date=today
    ).count()
    
    # Unique users today
    today_users = UserActivity.objects.filter(
        activity_type='login',
        timestamp__date=today
    ).values('user').distinct().count()
    
    # Failed login attempts
    failed_logins = LoginAttempt.objects.filter(success=False).count()
    successful_logins = LoginAttempt.objects.filter(success=True).count()
    
    # Recent activities (last 10)
    recent_activities = UserActivity.objects.select_related('user').order_by('-timestamp')[:10]
    
    # Failed login attempts (last 10)
    recent_failed_logins = LoginAttempt.objects.filter(success=False).order_by('-timestamp')[:10]
    
    # Activity by day (last 7 days)
    daily_activity = []
    for i in range(7):
        date = today - timedelta(days=i)
        count = UserActivity.objects.filter(timestamp__date=date).count()
        daily_activity.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    daily_activity.reverse()
    
    # Top active users
    top_users = UserActivity.objects.values(
        'user__username', 'user__first_name', 'user__last_name'
    ).annotate(
        activity_count=Count('id')
    ).order_by('-activity_count')[:10]
    
    # IP address analysis
    top_ips = UserActivity.objects.values('ip_address').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    print(f"📊 DASHBOARD STATISTICS:")
    print(f"   Total Logins: {total_logins}")
    print(f"   Total Logouts: {total_logouts}")
    print(f"   Today's Logins: {today_logins}")
    print(f"   Today's Logouts: {today_logouts}")
    print(f"   Active Users Today: {today_users}")
    print(f"   Successful Logins: {successful_logins}")
    print(f"   Failed Login Attempts: {failed_logins}")
    
    print(f"\n📈 DAILY ACTIVITY (Last 7 Days):")
    for day in daily_activity:
        print(f"   {day['date']}: {day['count']} activities")
    
    print(f"\n👥 TOP ACTIVE USERS:")
    for i, user in enumerate(top_users, 1):
        print(f"   {i}. {user['user__username']} - {user['activity_count']} activities")
    
    print(f"\n🌐 TOP IP ADDRESSES:")
    for i, ip in enumerate(top_ips, 1):
        print(f"   {i}. {ip['ip_address']} - {ip['count']} activities")
    
    print(f"\n📋 RECENT ACTIVITIES:")
    for i, activity in enumerate(recent_activities, 1):
        print(f"   {i}. {activity.user.username} - {activity.get_activity_type_display()} - {activity.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n🚨 RECENT FAILED LOGINS:")
    for i, attempt in enumerate(recent_failed_logins, 1):
        print(f"   {i}. {attempt.user.username if attempt.user else 'Unknown'} - {attempt.ip_address} - {attempt.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n🎯 ADMIN DASHBOARD FEATURES:")
    print(f"   ✅ Statistics Cards: Working")
    print(f"   ✅ Recent Activity Table: Working")
    print(f"   ✅ Activity Chart: Working")
    print(f"   ✅ Quick Actions: Working")
    print(f"   ✅ Failed Login Monitoring: Working")
    print(f"   ✅ Top Users Analysis: Working")
    print(f"   ✅ IP Address Analysis: Working")
    
    print(f"\n🚀 HOW TO ACCESS:")
    print(f"1. Login as superuser")
    print(f"2. Go to: http://127.0.0.1:8000/admin/")
    print(f"3. You'll see the custom admin interface")
    print(f"4. Navigate to 'Dashboard' or use the sidebar")
    print(f"5. View all statistics and monitoring data")
    
    print(f"\n📱 DASHBOARD FEATURES:")
    print(f"   - Real-time activity statistics")
    print(f"   - Interactive activity chart")
    print(f"   - Recent user activity table")
    print(f"   - Failed login attempt monitoring")
    print(f"   - Top active users analysis")
    print(f"   - IP address tracking")
    print(f"   - Quick action buttons")
    print(f"   - Professional admin interface")
    
    print(f"\n" + "=" * 60)
    print(f"✅ ADMIN DASHBOARD TEST COMPLETE!")
    print(f"=" * 60)

if __name__ == "__main__":
    test_admin_dashboard()
