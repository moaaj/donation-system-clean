def user_role_context(request):
    """
    Context processor to add user role information to all templates.
    This allows templates to conditionally show/hide content based on user roles.
    Made more robust to prevent interference with search functionality.
    """
    context = {
        'user_role': None,
        'is_admin': False,
        'is_student': False,
        'is_waqaf_admin': False,
        'is_donation_admin': False,
        'is_superuser': False,
        'user_profile': None,
    }
    
    if request.user.is_authenticated:
        try:
            # Set basic Django permissions first
            context.update({
                'is_admin': request.user.is_staff,
                'is_superuser': request.user.is_superuser,
            })
            
            # Try to get profile from accounts app first
            profile = getattr(request.user, 'profile', None)
            if profile and hasattr(profile, 'role'):
                context.update({
                    'user_role': profile.role,
                    'is_admin': profile.is_admin() if hasattr(profile, 'is_admin') else request.user.is_staff,
                    'is_student': profile.role == 'student',
                    'is_waqaf_admin': profile.is_waqaf_admin() if hasattr(profile, 'is_waqaf_admin') else False,
                    'is_donation_admin': profile.is_donation_admin() if hasattr(profile, 'is_donation_admin') else False,
                    'is_superuser': profile.is_superuser() if hasattr(profile, 'is_superuser') else request.user.is_superuser,
                    'user_profile': profile,
                    'can_access_main_admin': (profile.is_superuser() if hasattr(profile, 'is_superuser') else request.user.is_superuser) or (profile.role in ['admin', 'superuser']),
                })
            else:
                # Fallback to myapp profile if accounts profile doesn't exist
                try:
                    profile = getattr(request.user, 'myapp_profile', None)
                    if profile and hasattr(profile, 'role'):
                        context.update({
                            'user_role': profile.role,
                            'is_admin': profile.role == 'admin' or request.user.is_staff,
                            'is_student': profile.role == 'student',
                            'is_waqaf_admin': False,  # myapp profile doesn't have waqaf admin role
                            'is_donation_admin': False,  # myapp profile doesn't have donation admin role
                            'user_profile': profile,
                        })
                except Exception:
                    # If myapp profile doesn't exist or has issues, keep Django defaults
                    pass
        except Exception as e:
            # If any error occurs, just use Django's built-in permissions
            # Don't let context processor errors break the application
            context.update({
                'is_admin': request.user.is_staff if hasattr(request.user, 'is_staff') else False,
                'is_superuser': request.user.is_superuser if hasattr(request.user, 'is_superuser') else False,
            })
    
    return context 