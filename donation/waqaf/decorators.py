from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from functools import wraps


def waqaf_admin_required(view_func):
    """
    Decorator to check if user is a waqaf admin.
    Redirects to login page with error message if not authorized.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        # Check if user is superuser
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        # Check if user has waqaf admin role
        try:
            profile = request.user.profile
            if profile.is_waqaf_admin() or profile.is_superuser():
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'Access denied. Waqaf admin privileges required.')
                return redirect('home')
        except:
            messages.error(request, 'User profile not found. Please contact administrator.')
            return redirect('home')
    
    return _wrapped_view


def waqaf_access_required(view_func):
    """
    Decorator to check if user has access to waqaf features.
    Allows both waqaf admins and superusers.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        # Check if user is superuser or staff
        if request.user.is_superuser or request.user.is_staff:
            return view_func(request, *args, **kwargs)
        
        # Check if user has waqaf admin role
        try:
            profile = request.user.profile
            if profile.is_waqaf_admin() or profile.is_superuser():
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'Access denied. Waqaf access privileges required.')
                return redirect('home')
        except:
            messages.error(request, 'User profile not found. Please contact administrator.')
            return redirect('home')
    
    return _wrapped_view
