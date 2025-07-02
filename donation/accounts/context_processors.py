def user_role_context(request):
    """
    Context processor to add user role information to all templates.
    This allows templates to conditionally show/hide content based on user roles.
    """
    context = {
        'user_role': None,
        'is_admin': False,
        'is_student': False,
        'user_profile': None,
    }
    
    if request.user.is_authenticated:
        try:
            profile = request.user.myapp_profile
            context.update({
                'user_role': profile.role,
                'is_admin': profile.role == 'admin',
                'is_student': profile.role == 'student',
                'user_profile': profile,
            })
        except:
            # If profile doesn't exist, user has no role
            pass
    
    return context 