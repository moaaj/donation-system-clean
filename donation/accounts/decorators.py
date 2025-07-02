from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from functools import wraps
from myapp.models import UserProfile


def admin_required(view_func):
    """
    Decorator to check if user is an admin.
    Redirects to home page with error message if not admin.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        try:
            profile = request.user.myapp_profile
            if profile.role == 'admin':
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'Access denied. Admin privileges required.')
                return redirect('home')
        except:
            messages.error(request, 'User profile not found. Please contact administrator.')
            return redirect('home')
    
    return _wrapped_view


def student_required(view_func):
    """
    Decorator to check if user is a student.
    Redirects to home page with error message if not student.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        try:
            profile = request.user.myapp_profile
            if profile.role == 'student':
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'Access denied. Student privileges required.')
                return redirect('home')
        except:
            messages.error(request, 'User profile not found. Please contact administrator.')
            return redirect('home')
    
    return _wrapped_view


def role_required(allowed_roles):
    """
    Decorator to check if user has one of the allowed roles.
    Usage: @role_required(['admin', 'student'])
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            
            try:
                profile = request.user.myapp_profile
                if profile.role in allowed_roles:
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(request, f'Access denied. Required roles: {", ".join(allowed_roles)}')
                    return redirect('home')
            except:
                messages.error(request, 'User profile not found. Please contact administrator.')
                return redirect('home')
        
        return _wrapped_view
    return decorator


def student_owns_payment(view_func):
    """
    Decorator to check if the student owns the payment they're trying to access.
    Assumes payment_id is passed as a parameter.
    """
    @wraps(view_func)
    def _wrapped_view(request, payment_id, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        try:
            profile = request.user.myapp_profile
            if profile.role == 'admin':
                # Admins can access all payments
                return view_func(request, payment_id, *args, **kwargs)
            elif profile.role == 'student':
                # Students can only access their own payments
                from myapp.models import Payment
                try:
                    payment = Payment.objects.get(id=payment_id, student=profile.student)
                    return view_func(request, payment_id, *args, **kwargs)
                except Payment.DoesNotExist:
                    messages.error(request, 'Payment not found or access denied.')
                    return redirect('myapp:payment_list')
            else:
                messages.error(request, 'Access denied.')
                return redirect('home')
        except:
            messages.error(request, 'User profile not found. Please contact administrator.')
            return redirect('home')
    
    return _wrapped_view


def student_owns_student_record(view_func):
    """
    Decorator to check if the student is accessing their own student record.
    Assumes student_id is passed as a parameter.
    """
    @wraps(view_func)
    def _wrapped_view(request, student_id, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        try:
            profile = request.user.myapp_profile
            if profile.role == 'admin':
                # Admins can access all student records
                return view_func(request, student_id, *args, **kwargs)
            elif profile.role == 'student':
                # Students can only access their own record
                if profile.student and str(profile.student.id) == str(student_id):
                    return view_func(request, student_id, *args, **kwargs)
                else:
                    messages.error(request, 'Access denied. You can only view your own records.')
                    return redirect('myapp:student_detail', student_id=profile.student.id if profile.student else 0)
            else:
                messages.error(request, 'Access denied.')
                return redirect('home')
        except:
            messages.error(request, 'User profile not found. Please contact administrator.')
            return redirect('home')
    
    return _wrapped_view 