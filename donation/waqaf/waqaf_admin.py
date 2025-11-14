from django.contrib.admin import AdminSite
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.template.response import TemplateResponse
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from .models import WaqafAsset, Contributor, Contribution, Payment, FundDistribution
from .admin import WaqafAssetAdmin, ContributorAdmin, ContributionAdmin, PaymentAdmin, FundDistributionAdmin


class WaqafAdminSite(AdminSite):
    """Custom admin site specifically for waqaf management"""
    
    site_header = "Waqaf Administration"
    site_title = "Waqaf Admin"
    index_title = "Waqaf Management Dashboard"
    index_template = 'waqaf/admin/dashboard.html'
    login_template = 'admin/login.html'
    logout_template = 'admin/logged_out.html'
    
    def __init__(self, name='waqaf_admin'):
        super().__init__(name)
        # Clear any existing registrations to ensure only waqaf models
        self._registry = {}
        self.register_models()
    
    def register_models(self):
        """Register only waqaf-related models"""
        self.register(WaqafAsset, WaqafAssetAdmin)
        self.register(Contributor, ContributorAdmin)
        self.register(Contribution, ContributionAdmin)
        self.register(Payment, PaymentAdmin)
        self.register(FundDistribution, FundDistributionAdmin)
    
    def get_app_list(self, request):
        """Override to show only waqaf-related apps"""
        # Only return waqaf app with its models
        waqaf_app = {
            'name': 'Waqaf',
            'app_label': 'waqaf',
            'app_url': '/waqaf-admin/',
            'has_module_perms': True,
            'models': []
        }
        
        # Add waqaf models
        waqaf_models = [
            {
                'name': 'Waqaf Assets',
                'object_name': 'waqafasset',
                'admin_url': '/waqaf-admin/waqaf/waqafasset/',
                'add_url': '/waqaf-admin/waqaf/waqafasset/add/',
                'view_only': False,
            },
            {
                'name': 'Contributors',
                'object_name': 'contributor',
                'admin_url': '/waqaf-admin/waqaf/contributor/',
                'add_url': '/waqaf-admin/waqaf/contributor/add/',
                'view_only': False,
            },
            {
                'name': 'Contributions',
                'object_name': 'contribution',
                'admin_url': '/waqaf-admin/waqaf/contribution/',
                'add_url': '/waqaf-admin/waqaf/contribution/add/',
                'view_only': False,
            },
            {
                'name': 'Payments',
                'object_name': 'payment',
                'admin_url': '/waqaf-admin/waqaf/payment/',
                'add_url': '/waqaf-admin/waqaf/payment/add/',
                'view_only': False,
            },
            {
                'name': 'Fund Distributions',
                'object_name': 'funddistribution',
                'admin_url': '/waqaf-admin/waqaf/funddistribution/',
                'add_url': '/waqaf-admin/waqaf/funddistribution/add/',
                'view_only': False,
            },
        ]
        
        waqaf_app['models'] = waqaf_models
        return [waqaf_app]
    
    def get_model_admin(self, model):
        """Override to ensure only waqaf models are accessible"""
        # Only return admin for waqaf models
        waqaf_models = [WaqafAsset, Contributor, Contribution, Payment, FundDistribution]
        if model in waqaf_models:
            return super().get_model_admin(model)
        return None
    
    def each_context(self, request):
        """Override to provide only waqaf-related context"""
        context = super().each_context(request)
        # Ensure only waqaf apps are shown
        context['available_apps'] = self.get_app_list(request)
        return context
    
    def has_permission(self, request):
        """Check if user has waqaf admin permissions"""
        if not request.user.is_authenticated:
            return False
        
        # Check if user is superuser or has waqaf_admin role
        if request.user.is_superuser:
            return True
        
        try:
            profile = request.user.profile
            return profile.is_waqaf_admin() or profile.is_superuser()
        except:
            return False
    
    def has_module_permission(self, request):
        """Check if user has permission to access waqaf module"""
        return self.has_permission(request)
    
    def has_view_permission(self, request, obj=None):
        """Check if user has view permission"""
        return self.has_permission(request)
    
    def has_add_permission(self, request):
        """Check if user has add permission"""
        return self.has_permission(request)
    
    def has_change_permission(self, request, obj=None):
        """Check if user has change permission"""
        return self.has_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        """Check if user has delete permission"""
        return self.has_permission(request)
    
    def index(self, request, extra_context=None):
        """Custom index page with waqaf-specific dashboard"""
        if not self.has_permission(request):
            messages.error(request, 'Access denied. Waqaf admin privileges required.')
            return redirect('accounts:login')
        
        # Get waqaf statistics
        total_assets = WaqafAsset.objects.count()
        active_assets = WaqafAsset.objects.filter(is_archived=False).count()
        archived_assets = WaqafAsset.objects.filter(is_archived=True).count()
        
        total_contributions = Contribution.objects.count()
        total_contributors = Contributor.objects.count()
        
        # Calculate total amount contributed
        total_amount = Contribution.objects.aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Get recent contributions
        recent_contributions = Contribution.objects.select_related(
            'contributor', 'asset'
        ).order_by('-date_contributed')[:10]
        
        # Get payment statistics
        total_payments = Payment.objects.count()
        completed_payments = Payment.objects.filter(status='COMPLETED').count()
        pending_payments = Payment.objects.filter(status='PENDING').count()
        overdue_payments = Payment.objects.filter(
            status='PENDING',
            due_date__lt=timezone.now().date()
        ).count()
        
        # Get monthly statistics
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        monthly_contributions = Contribution.objects.filter(
            date_contributed__gte=thirty_days_ago
        ).count()
        monthly_amount = Contribution.objects.filter(
            date_contributed__gte=thirty_days_ago
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Get top assets by contributions
        top_assets = WaqafAsset.objects.annotate(
            contribution_count=Count('contribution'),
            total_contributed=Sum('contribution__amount')
        ).order_by('-contribution_count')[:5]
        
        context = {
            'title': 'Waqaf Management Dashboard',
            'total_assets': total_assets,
            'active_assets': active_assets,
            'archived_assets': archived_assets,
            'total_contributions': total_contributions,
            'total_contributors': total_contributors,
            'total_amount': total_amount,
            'recent_contributions': recent_contributions,
            'total_payments': total_payments,
            'completed_payments': completed_payments,
            'pending_payments': pending_payments,
            'overdue_payments': overdue_payments,
            'monthly_contributions': monthly_contributions,
            'monthly_amount': monthly_amount,
            'top_assets': top_assets,
            'app_list': self.get_app_list(request),
        }
        
        if extra_context:
            context.update(extra_context)
        
        return TemplateResponse(request, 'waqaf/admin/dashboard.html', context)
    
    def get_urls(self):
        """Add custom URLs for waqaf admin"""
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.index), name='waqaf_dashboard'),
            path('analytics/', self.admin_view(self.analytics_view), name='waqaf_analytics'),
            path('reports/', self.admin_view(self.reports_view), name='waqaf_reports'),
        ]
        return custom_urls + urls
    
    def analytics_view(self, request):
        """Advanced analytics view for waqaf admin"""
        if not self.has_permission(request):
            messages.error(request, 'Access denied. Waqaf admin privileges required.')
            return redirect('accounts:login')
        
        # Get detailed analytics data
        context = {
            'title': 'Waqaf Analytics',
            'app_list': self.get_app_list(request),
        }
        
        return TemplateResponse(request, 'waqaf/admin/analytics.html', context)
    
    def reports_view(self, request):
        """Reports view for waqaf admin"""
        if not self.has_permission(request):
            messages.error(request, 'Access denied. Waqaf admin privileges required.')
            return redirect('accounts:login')
        
        context = {
            'title': 'Waqaf Reports',
            'app_list': self.get_app_list(request),
        }
        
        return TemplateResponse(request, 'waqaf/admin/reports.html', context)


# Create the waqaf admin site instance
waqaf_admin_site = WaqafAdminSite()
