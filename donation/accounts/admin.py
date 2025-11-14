from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import UserProfile, LoginAttempt, UserActivity

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'is_verified', 'created_at')
    list_filter = ('is_verified', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'success', 'timestamp')
    list_filter = ('success', 'timestamp')
    search_fields = ('user__username', 'ip_address')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    
    def has_add_permission(self, request):
        return False  # Don't allow manual creation of login attempts

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'ip_address', 'timestamp')
    list_filter = ('activity_type', 'timestamp')
    search_fields = ('user__username', 'user__email', 'ip_address')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    
    def has_add_permission(self, request):
        return False  # Don't allow manual creation of user activities
    
    def has_change_permission(self, request, obj=None):
        return False  # Don't allow editing of user activities
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Only superusers can delete activities

# Custom Admin Site with Dashboard
class CustomAdminSite(AdminSite):
    site_header = "School Management System Admin"
    site_title = "School Admin Portal"
    index_title = "Welcome to School Management Dashboard"
    
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name='dashboard'),
        ]
        return custom_urls + urls
    
    def dashboard_view(self, request):
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
        
        # Recent activities (last 20 for more detail)
        recent_activities = UserActivity.objects.select_related('user').order_by('-timestamp')[:20]
        
        # Failed login attempts (last 10)
        recent_failed_logins = LoginAttempt.objects.filter(success=False).order_by('-timestamp')[:10]
        
        # Activity by day (last 7 days)
        last_7_days = now - timedelta(days=7)
        daily_activity = []
        for i in range(7):
            date = today - timedelta(days=i)
            count = UserActivity.objects.filter(timestamp__date=date).count()
            daily_activity.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': count
            })
        daily_activity.reverse()
        
        # Top active users with more details
        top_users = UserActivity.objects.values(
            'user__username', 'user__first_name', 'user__last_name'
        ).annotate(
            activity_count=Count('id'),
            login_count=Count('id', filter=Q(activity_type='login')),
            logout_count=Count('id', filter=Q(activity_type='logout'))
        ).order_by('-activity_count')[:10]
        
        # IP address analysis
        top_ips = UserActivity.objects.values('ip_address').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Specific user activity (tamim123)
        try:
            tamim123 = User.objects.get(username='tamim123')
            tamim123_activities = UserActivity.objects.filter(user=tamim123).order_by('-timestamp')[:10]
            tamim123_stats = {
                'total_activities': UserActivity.objects.filter(user=tamim123).count(),
                'logins': UserActivity.objects.filter(user=tamim123, activity_type='login').count(),
                'logouts': UserActivity.objects.filter(user=tamim123, activity_type='logout').count(),
                'today_activities': UserActivity.objects.filter(user=tamim123, timestamp__date=today).count(),
            }
        except User.DoesNotExist:
            tamim123_activities = []
            tamim123_stats = {'total_activities': 0, 'logins': 0, 'logouts': 0, 'today_activities': 0}
        
        # All users with their activity counts
        from django.contrib.auth.models import User
        from django.db.models import Max
        all_users_activity = UserActivity.objects.values(
            'user__username', 'user__first_name', 'user__last_name'
        ).annotate(
            total_activities=Count('id'),
            login_count=Count('id', filter=Q(activity_type='login')),
            logout_count=Count('id', filter=Q(activity_type='logout')),
            last_activity=Max('timestamp')
        ).order_by('-total_activities')
        
        context = {
            'total_logins': total_logins,
            'total_logouts': total_logouts,
            'today_logins': today_logins,
            'today_logouts': today_logouts,
            'today_users': today_users,
            'failed_logins': failed_logins,
            'successful_logins': successful_logins,
            'recent_activities': recent_activities,
            'recent_failed_logins': recent_failed_logins,
            'daily_activity': daily_activity,
            'top_users': top_users,
            'top_ips': top_ips,
            'tamim123_activities': tamim123_activities,
            'tamim123_stats': tamim123_stats,
            'all_users_activity': all_users_activity,
            'current_time': now,
            'title': 'Admin Dashboard',
            'opts': self._registry[UserActivity]._meta,
        }
        
        return render(request, 'admin/dashboard.html', context)

# Create custom admin site instance
custom_admin_site = CustomAdminSite(name='custom_admin')

# Register models with custom admin site
custom_admin_site.register(UserProfile, UserProfileAdmin)
custom_admin_site.register(LoginAttempt, LoginAttemptAdmin)
custom_admin_site.register(UserActivity, UserActivityAdmin)

# Register all myapp models with custom admin site to avoid navbar conflicts
from myapp.models import (
    Student, Parent, FeeCategory, FeeStructure, Payment, PaymentReceipt, 
    Invoice, FeeDiscount, PaymentReminder, SchoolBankAccount, 
    DonationEvent, DonationCategory, IndividualStudentFee, PredefinedDonationAmount,
    PibgDonationSettings, PibgDonation, UserProfile, ModulePermission, SchoolFeesLevelAdmin
)
from myapp.admin import (
    StudentAdmin, ParentAdmin, FeeCategoryAdmin, FeeStructureAdmin, PaymentAdmin,
    PaymentReceiptAdmin, InvoiceAdmin, FeeDiscountAdmin, PaymentReminderAdmin,
    SchoolBankAccountAdmin, DonationEventAdmin, IndividualStudentFeeAdmin, PredefinedDonationAmountAdmin,
    PibgDonationSettingsAdmin, PibgDonationAdmin, UserProfileAdmin, ModulePermissionAdmin, SchoolFeesLevelAdminAdmin
)
from donation2.models import Donor, Donation, Transaction

# Register myapp models
custom_admin_site.register(Student, StudentAdmin)
custom_admin_site.register(Parent, ParentAdmin)
custom_admin_site.register(FeeCategory, FeeCategoryAdmin)
custom_admin_site.register(FeeStructure, FeeStructureAdmin)
custom_admin_site.register(Payment, PaymentAdmin)
custom_admin_site.register(PaymentReceipt, PaymentReceiptAdmin)
custom_admin_site.register(Invoice, InvoiceAdmin)
custom_admin_site.register(FeeDiscount, FeeDiscountAdmin)
custom_admin_site.register(PaymentReminder, PaymentReminderAdmin)
custom_admin_site.register(SchoolBankAccount, SchoolBankAccountAdmin)
custom_admin_site.register(DonationEvent, DonationEventAdmin)
custom_admin_site.register(DonationCategory)
custom_admin_site.register(IndividualStudentFee, IndividualStudentFeeAdmin)
custom_admin_site.register(PredefinedDonationAmount, PredefinedDonationAmountAdmin)

# Register PIBG Donation models
custom_admin_site.register(PibgDonationSettings, PibgDonationSettingsAdmin)
custom_admin_site.register(PibgDonation, PibgDonationAdmin)

# Register Enhanced User Management models
custom_admin_site.register(UserProfile, UserProfileAdmin)
custom_admin_site.register(ModulePermission, ModulePermissionAdmin)
custom_admin_site.register(SchoolFeesLevelAdmin, SchoolFeesLevelAdminAdmin)

# Register donation2 models
custom_admin_site.register(Donor)
custom_admin_site.register(Donation)
custom_admin_site.register(Transaction)

# Register waqaf models with custom admin site
from waqaf.models import WaqafAsset, Contributor, FundDistribution, Contribution, Payment as WaqafPayment
from waqaf.admin import WaqafAssetAdmin, ContributorAdmin, FundDistributionAdmin, ContributionAdmin, PaymentAdmin as WaqafPaymentAdmin

custom_admin_site.register(WaqafAsset, WaqafAssetAdmin)
custom_admin_site.register(Contributor, ContributorAdmin)
custom_admin_site.register(FundDistribution, FundDistributionAdmin)
custom_admin_site.register(Contribution, ContributionAdmin)
custom_admin_site.register(WaqafPayment, WaqafPaymentAdmin)

# Register Django auth models with custom admin site
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin

custom_admin_site.register(User, UserAdmin)
custom_admin_site.register(Group, GroupAdmin)
