from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import EnhancedUserCreationForm
from .models import UserProfile, ModulePermission, SchoolFeesLevelAdmin

def is_super_admin(user):
    """Check if user is a super admin"""
    return user.is_authenticated and user.is_superuser

@login_required
@user_passes_test(is_super_admin)
def create_module_admin(request):
    """Create a new module admin user"""
    if request.method == 'POST':
        form = EnhancedUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Successfully created admin user: {user.username}')
            return redirect('admin:myapp_userprofile_changelist')
    else:
        form = EnhancedUserCreationForm()
    
    context = {
        'form': form,
        'title': 'Create Module Admin',
    }
    return render(request, 'myapp/create_module_admin.html', context)

@login_required
@user_passes_test(is_super_admin)
def admin_dashboard(request):
    """Enhanced admin dashboard with module admin overview"""
    # Get all module admins
    module_admins = UserProfile.objects.filter(
        role__in=['donation_admin', 'waqaf_admin', 'school_fees_admin', 'school_fees_level_admin']
    ).select_related('user')
    
    # Get module permissions
    module_permissions = ModulePermission.objects.select_related('user_profile__user')
    
    # Get level admin assignments
    level_admins = SchoolFeesLevelAdmin.objects.select_related('user_profile__user')
    
    # Statistics
    total_admins = module_admins.count()
    donation_admins = module_admins.filter(role='donation_admin').count()
    waqaf_admins = module_admins.filter(role='waqaf_admin').count()
    school_fees_admins = module_admins.filter(role='school_fees_admin').count()
    level_admins_count = module_admins.filter(role='school_fees_level_admin').count()
    
    context = {
        'module_admins': module_admins,
        'module_permissions': module_permissions,
        'level_admins': level_admins,
        'total_admins': total_admins,
        'donation_admins': donation_admins,
        'waqaf_admins': waqaf_admins,
        'school_fees_admins': school_fees_admins,
        'level_admins_count': level_admins_count,
    }
    return render(request, 'myapp/admin_dashboard.html', context)
