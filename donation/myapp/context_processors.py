"""
Context processors for the myapp app
"""

def user_roles(request):
    """
    Add user role information to template context
    """
    context = {
        'is_waqaf_admin': False,
        'is_donation_admin': False,
        'is_form1_admin': False,
        'is_form3_admin': False,
        'can_access_main_admin': False,
    }
    
    if request.user.is_authenticated:
        try:
            # Get user profile
            profile = getattr(request.user, 'profile', None)
            if profile:
                context['is_waqaf_admin'] = profile.is_waqaf_admin()
                context['is_donation_admin'] = profile.is_donation_admin()
                context['is_form1_admin'] = profile.is_form1_admin()
                context['is_form3_admin'] = profile.is_form3_admin()
                context['can_access_main_admin'] = (
                    request.user.is_superuser or 
                    request.user.is_staff or 
                    profile.is_admin()
                )
        except Exception:
            # If there's any error getting profile, use defaults
            pass
    
    return context
