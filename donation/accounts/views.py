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
    UserProfileForm, PasswordChangeRequestForm, PasswordResetForm
)
from .models import UserProfile, LoginAttempt


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


@csrf_protect
@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password1']
        user = User.objects.create_user(username=username, password=password)
        return redirect('accounts:login')
    return render(request, 'accounts/register.html')


@csrf_protect
@require_http_methods(["GET", "POST"])
def login_view(request):
    """Enhanced login view with security features"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
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
    logout(request)
    messages.success(request, f'You have been successfully logged out. Goodbye, {user.get_full_name() or user.username}!')
    return redirect('login')


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