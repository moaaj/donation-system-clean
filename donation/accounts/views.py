from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
import json
from .forms import (
    EnhancedUserCreationForm, EnhancedAuthenticationForm, 
    UserProfileForm, PasswordChangeRequestForm, PasswordResetForm,
    RoleBasedRegistrationForm
)
from .models import UserProfile, LoginAttempt, UserActivity
from myapp.models import Student, UserProfile as MyAppUserProfile


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_login_attempt(request, user, success):
    """Log login attempt for security monitoring"""
    try:
        LoginAttempt.objects.create(
            user=user if success else None,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=success
        )
    except Exception as e:
        # Log error but don't break the login process
        print(f"Error logging login attempt: {e}")

def log_user_activity(request, user, activity_type):
    """Log user activity for superuser monitoring"""
    try:
        UserActivity.objects.create(
            user=user,
            activity_type=activity_type,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    except Exception as e:
        # Log error but don't break the process
        print(f"Error logging user activity: {e}")


@csrf_protect
@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.method == 'POST':
        form = RoleBasedRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create the user
                    user = form.save(commit=False)
                    user.first_name = form.cleaned_data['first_name']
                    user.last_name = form.cleaned_data['last_name']
                    user.email = form.cleaned_data['email']
                    user.save()
                    
                    # Create user profile
                    role = form.cleaned_data['role']
                    phone_number = form.cleaned_data.get('phone_number', '')
                    address = form.cleaned_data.get('address', '')
                    
                    # Update the automatically created profile in accounts app
                    profile, created = UserProfile.objects.get_or_create(
                        user=user,
                        defaults={
                            'phone_number': phone_number,
                            'address': address
                        }
                    )
                    if not created:
                        # Update existing profile
                        profile.phone_number = phone_number
                        profile.address = address
                        profile.save()
                    
                    # Create profile in myapp with role
                    myapp_profile = MyAppUserProfile.objects.create(
                        user=user,
                        role=role,
                        phone_number=phone_number,
                        address=address
                    )
                    
                    # If student role, create or link student record with form level
                    if role == 'student':
                        student_id = form.cleaned_data['student_id']
                        form_level = form.cleaned_data['form_level']
                        
                        # Check if student already exists
                        student, created = Student.objects.get_or_create(
                            student_id=student_id,
                            defaults={
                                'first_name': user.first_name,
                                'last_name': user.last_name,
                                'year_batch': timezone.now().year,
                                'nric': f"T{student_id[:10]}",  # Shorter NRIC format
                                'level': 'form',  # Set level to 'form'
                                'level_custom': form_level,  # Set the selected form level
                                'is_active': True
                            }
                        )
                        
                        # If student was updated (not created), update the form level
                        if not created:
                            student.level = 'form'
                            student.level_custom = form_level
                            student.save()
                        
                        # Link student to profile
                        myapp_profile.student = student
                        myapp_profile.save()
                        
                        # Automatically generate fees for the selected form level
                        if form_level:
                            from myapp.models import FeeStructure, FeeStatus
                            from datetime import date, timedelta
                            
                            # Get fee structures for this form level
                            form_fees = FeeStructure.objects.filter(
                                form__iexact=form_level,
                                is_active=True
                            )
                            
                            generated_count = 0
                            for fee_structure in form_fees:
                                # Check if fee status already exists
                                existing_status = FeeStatus.objects.filter(
                                    student=student,
                                    fee_structure=fee_structure
                                ).first()
                                
                                if not existing_status:
                                    # Calculate due date based on frequency
                                    if fee_structure.frequency == 'yearly':
                                        due_date = date.today() + timedelta(days=30)  # 30 days from now
                                    elif fee_structure.frequency == 'termly':
                                        due_date = date.today() + timedelta(days=90)  # 90 days from now
                                    elif fee_structure.frequency == 'monthly':
                                        due_date = date.today() + timedelta(days=30)  # 30 days from now
                                    else:
                                        due_date = date.today() + timedelta(days=30)
                                    
                                    # Create fee status
                                    FeeStatus.objects.create(
                                        student=student,
                                        fee_structure=fee_structure,
                                        amount=fee_structure.amount or 0,
                                        due_date=due_date,
                                        status='pending'
                                    )
                                    generated_count += 1
                            
                            if generated_count > 0:
                                messages.success(request, f'Account created successfully! You can now login as a student. {generated_count} fee records have been automatically generated for {form_level}.')
                            else:
                                messages.success(request, f'Account created successfully! You can now login as a student. You have been assigned to {form_level}.')
                        else:
                            messages.success(request, 'Account created successfully! You can now login as a student.')
                    
                    # Set admin permissions if admin role
                    if role in ['admin', 'donation_admin', 'waqaf_admin', 'school_fees_admin', 'school_fees_level_admin']:
                        user.is_staff = True
                        user.save()
                        
                        # Handle school fees level admin level assignment
                        if role == 'school_fees_level_admin':
                            admin_level = form.cleaned_data.get('admin_level')
                            if admin_level:
                                from myapp.models import SchoolFeesLevelAdmin
                                SchoolFeesLevelAdmin.objects.create(
                                    user_profile=myapp_profile,
                                    level=admin_level,
                                    can_view=True,
                                    can_add=True,
                                    can_change=True,
                                    can_delete=True,
                                    can_manage_fees=True,
                                    can_manage_payments=True
                                )
                                messages.success(request, f'Account created successfully! You can now login as a School Fees Level Admin for {admin_level}.')
                            else:
                                messages.success(request, 'Account created successfully! You can now login as a School Fees Level Admin.')
                        else:
                            # Set up module permissions for other admin roles
                            from myapp.models import ModulePermission
                            module_mapping = {
                                'donation_admin': 'donation',
                                'waqaf_admin': 'waqaf',
                                'school_fees_admin': 'school_fees',
                            }
                            
                            if role in module_mapping:
                                ModulePermission.objects.create(
                                    user_profile=myapp_profile,
                                    module=module_mapping[role],
                                    can_view=True,
                                    can_add=True,
                                    can_change=True,
                                    can_delete=True,
                                    can_manage_settings=True
                                )
                                
                                # Also add PIBG donation permissions for donation admin
                                if role == 'donation_admin':
                                    ModulePermission.objects.create(
                                        user_profile=myapp_profile,
                                        module='pibg_donation',
                                        can_view=True,
                                        can_add=True,
                                        can_change=True,
                                        can_delete=True,
                                        can_manage_settings=True
                                    )
                            
                            messages.success(request, f'Account created successfully! You can now login as a {role.replace("_", " ").title()}.')
                    else:
                        messages.success(request, 'Account created successfully! You can now login.')
                    
                    return redirect('accounts:login')
                    
            except Exception as e:
                print(f"Error during registration: {str(e)}")
                import traceback
                traceback.print_exc()
                messages.error(request, f'Error creating account: {str(e)}')
                return redirect('accounts:register')
        else:
            print(f"Form validation failed: {form.errors}")
    else:
        form = RoleBasedRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


@csrf_protect
@require_http_methods(["GET", "POST"])
def login_view(request):
    """Enhanced login view with security features"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = EnhancedAuthenticationForm(request.POST)
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Log successful login activity
            log_user_activity(request, user, 'login')
            messages.success(request, f'Hello {user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = EnhancedAuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """Enhanced logout view"""
    user = request.user
    # Log logout activity before logging out
    log_user_activity(request, user, 'logout')
    logout(request)
    messages.success(request, f'You have been successfully logged out. Goodbye, {user.get_full_name() or user.username}!')
    return redirect('/accounts/login/?next=/')  # Redirect to login with next parameter


@login_required
def profile_view(request):
    """User profile view"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user.profile)
    
    # Get user statistics
    user_stats = {
        'total_logins': LoginAttempt.objects.filter(user=request.user, success=True).count(),
        'last_login': LoginAttempt.objects.filter(user=request.user, success=True).first(),
        'account_age': timezone.now() - request.user.date_joined,
    }
    
    context = {
        'form': form,
        'user_stats': user_stats,
    }
    return render(request, 'accounts/profile.html', context)


def password_reset_request(request):
    """Password reset request view"""
    if request.method == 'POST':
        form = PasswordChangeRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.get(email=email)
            
            # Generate password reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Create reset URL
            reset_url = request.build_absolute_uri(
                f'/accounts/password-reset-confirm/{uid}/{token}/'
            )
            
            # Send password reset email
            try:
                send_password_reset_email(user, reset_url)
                messages.success(request, 'Password reset instructions have been sent to your email.')
            except Exception as e:
                messages.error(request, 'Error sending password reset email. Please try again.')
                print(f"Error sending password reset email: {e}")
            
            return redirect('login')
    else:
        form = PasswordChangeRequestForm()
    
    return render(request, 'accounts/password_reset_request.html', {'form': form})


def password_reset_confirm(request, uidb64, token):
    """Password reset confirmation view"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = PasswordResetForm(request.POST)
            if form.is_valid():
                user.set_password(form.cleaned_data['new_password1'])
                user.save()
                messages.success(request, 'Your password has been reset successfully. You can now login with your new password.')
                return redirect('login')
        else:
            form = PasswordResetForm()
        
        return render(request, 'accounts/password_reset_confirm.html', {'form': form})
    else:
        messages.error(request, 'The password reset link is invalid or has expired.')
        return redirect('login')


@login_required
def change_password(request):
    """Change password view for logged-in users"""
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            request.user.set_password(form.cleaned_data['new_password1'])
            request.user.save()
            messages.success(request, 'Your password has been changed successfully.')
            return redirect('profile')
    else:
        form = PasswordResetForm()
    
    return render(request, 'accounts/change_password.html', {'form': form})


def send_welcome_email(user):
    """Send welcome email to new user"""
    subject = 'Welcome to Our Platform!'
    message = f"""
    Hello {user.get_full_name() or user.username},
    
    Welcome to our platform! Your account has been created successfully.
    
    You can now login and start using our services.
    
    Best regards,
    The Team
    """
    
    send_mail(
        subject,
        message,
        'noreply@example.com',
        [user.email],
        fail_silently=False,
    )


def send_password_reset_email(user, reset_url):
    """Send password reset email"""
    subject = 'Password Reset Request'
    message = f"""
    Hello {user.get_full_name() or user.username},
    
    You requested a password reset for your account.
    
    Please click the following link to reset your password:
    {reset_url}
    
    If you didn't request this, please ignore this email.
    
    This link will expire in 24 hours.
    
    Best regards,
    The Team
    """
    
    send_mail(
        subject,
        message,
        'noreply@example.com',
        [user.email],
        fail_silently=False,
    )


# API views for AJAX requests
@require_http_methods(["POST"])
def check_username_availability(request):
    """Check if username is available (AJAX)"""
    data = json.loads(request.body)
    username = data.get('username', '')
    
    if User.objects.filter(username=username).exists():
        return JsonResponse({'available': False})
    else:
        return JsonResponse({'available': True})


@require_http_methods(["POST"])
def check_email_availability(request):
    """Check if email is available (AJAX)"""
    data = json.loads(request.body)
    email = data.get('email', '')
    
    if User.objects.filter(email=email).exists():
        return JsonResponse({'available': False})
    else:
        return JsonResponse({'available': True})


@login_required
def superuser_dashboard(request):
    """Dashboard for superuser to monitor user activity"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser privileges required.')
        return redirect('home')
    
    # Get recent user activity
    recent_activities = UserActivity.objects.select_related('user').order_by('-timestamp')[:50]
    
    # Get login statistics
    total_logins = UserActivity.objects.filter(activity_type='login').count()
    total_logouts = UserActivity.objects.filter(activity_type='logout').count()
    
    # Get today's activity
    from datetime import datetime, timedelta
    today = datetime.now().date()
    today_logins = UserActivity.objects.filter(
        activity_type='login',
        timestamp__date=today
    ).count()
    today_logouts = UserActivity.objects.filter(
        activity_type='logout',
        timestamp__date=today
    ).count()
    
    # Get unique users who logged in today
    today_users = UserActivity.objects.filter(
        activity_type='login',
        timestamp__date=today
    ).values('user').distinct().count()
    
    # Get failed login attempts
    failed_logins = LoginAttempt.objects.filter(success=False).order_by('-timestamp')[:20]
    
    context = {
        'recent_activities': recent_activities,
        'total_logins': total_logins,
        'total_logouts': total_logouts,
        'today_logins': today_logins,
        'today_logouts': today_logouts,
        'today_users': today_users,
        'failed_logins': failed_logins,
    }
    
    return render(request, 'accounts/superuser_dashboard.html', context) 


def public_activity_dashboard(request):
    """Superuser-only dashboard showing all user activities"""
    # Check if user is superuser
    if not request.user.is_authenticated or not request.user.is_superuser:
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, 'Access denied. Only superusers can view this dashboard.')
        return redirect('home')
    
    from django.utils import timezone
    from datetime import datetime, timedelta
    from django.db.models import Count, Q, Max
    from django.contrib.auth.models import User
    
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
    
    # Recent activities (last 30 for more detail)
    recent_activities = UserActivity.objects.select_related('user').order_by('-timestamp')[:30]
    
    # Failed login attempts (last 15)
    recent_failed_logins = LoginAttempt.objects.filter(success=False).order_by('-timestamp')[:15]
    
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
    
    # Top active users with more details
    top_users = UserActivity.objects.values(
        'user__username', 'user__first_name', 'user__last_name'
    ).annotate(
        activity_count=Count('id'),
        login_count=Count('id', filter=Q(activity_type='login')),
        logout_count=Count('id', filter=Q(activity_type='logout'))
    ).order_by('-activity_count')[:15]
    
    # IP address analysis
    top_ips = UserActivity.objects.values('ip_address').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Specific user activity (tamim123)
    try:
        tamim123 = User.objects.get(username='tamim123')
        tamim123_activities = UserActivity.objects.filter(user=tamim123).order_by('-timestamp')[:15]
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
    }
    
    return render(request, 'accounts/public_activity_dashboard.html', context) 