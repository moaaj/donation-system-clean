from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from accounts.decorators import admin_required, student_required, role_required, student_owns_payment, student_owns_student_record
from .models import Student, Payment, FeeStructure, FeeCategory, DonationEvent, Donation
from .forms import PaymentForm, StudentForm, FeeStructureForm


# ============================================================================
# ADMIN-ONLY VIEWS
# ============================================================================

@admin_required
def admin_dashboard(request):
    """Admin dashboard - only accessible by admins"""
    context = {
        'total_students': Student.objects.count(),
        'total_payments': Payment.objects.count(),
        'total_donations': Donation.objects.count(),
        'recent_payments': Payment.objects.all().order_by('-created_at')[:5],
        'recent_students': Student.objects.all().order_by('-created_at')[:5],
    }
    return render(request, 'myapp/admin_dashboard.html', context)


@admin_required
def student_management(request):
    """Student management - only accessible by admins"""
    students = Student.objects.all().order_by('-created_at')
    context = {
        'students': students,
    }
    return render(request, 'myapp/student_management.html', context)


@admin_required
def fee_structure_management(request):
    """Fee structure management - only accessible by admins"""
    fee_structures = FeeStructure.objects.all().order_by('-created_at')
    context = {
        'fee_structures': fee_structures,
    }
    return render(request, 'myapp/fee_structure_management.html', context)


@admin_required
def payment_reports(request):
    """Payment reports - only accessible by admins"""
    payments = Payment.objects.all().order_by('-created_at')
    context = {
        'payments': payments,
    }
    return render(request, 'myapp/payment_reports.html', context)


# ============================================================================
# STUDENT-ONLY VIEWS
# ============================================================================

@student_required
def student_dashboard(request):
    """Student dashboard - only accessible by students"""
    try:
        student = request.user.myapp_profile.student
        student_payments = Payment.objects.filter(student=student).order_by('-created_at')
        
        context = {
            'student': student,
            'recent_payments': student_payments[:5],
            'total_payments': student_payments.count(),
            'total_paid': sum(payment.amount for payment in student_payments if payment.status == 'completed'),
        }
        return render(request, 'myapp/student_dashboard.html', context)
    except:
        messages.error(request, 'Student profile not found.')
        return redirect('home')


@student_required
def student_payment_history(request):
    """Student payment history - only accessible by students"""
    try:
        student = request.user.myapp_profile.student
        payments = Payment.objects.filter(student=student).order_by('-created_at')
        
        context = {
            'payments': payments,
            'student': student,
        }
        return render(request, 'myapp/student_payment_history.html', context)
    except:
        messages.error(request, 'Student profile not found.')
        return redirect('home')


@student_required
def make_payment(request):
    """Make payment - only accessible by students"""
    try:
        student = request.user.myapp_profile.student
        
        if request.method == 'POST':
            form = PaymentForm(request.POST)
            if form.is_valid():
                payment = form.save(commit=False)
                payment.student = student
                payment.save()
                messages.success(request, 'Payment submitted successfully!')
                return redirect('myapp:student_payment_history')
        else:
            form = PaymentForm()
        
        context = {
            'form': form,
            'student': student,
        }
        return render(request, 'myapp/make_payment.html', context)
    except:
        messages.error(request, 'Student profile not found.')
        return redirect('home')


# ============================================================================
# ROLE-BASED VIEWS (Multiple roles can access)
# ============================================================================

@role_required(['admin', 'student'])
def payment_detail(request, payment_id):
    """Payment detail - accessible by admins and the student who owns the payment"""
    payment = get_object_or_404(Payment, id=payment_id)
    
    # Additional check for students - they can only see their own payments
    if request.user.myapp_profile.role == 'student':
        if payment.student != request.user.myapp_profile.student:
            messages.error(request, 'Access denied. You can only view your own payments.')
            return redirect('myapp:student_payment_history')
    
    context = {
        'payment': payment,
    }
    return render(request, 'myapp/payment_detail.html', context)


@role_required(['admin', 'student'])
def student_detail(request, student_id):
    """Student detail - accessible by admins and the student themselves"""
    student = get_object_or_404(Student, id=student_id)
    
    # Additional check for students - they can only see their own details
    if request.user.myapp_profile.role == 'student':
        if student != request.user.myapp_profile.student:
            messages.error(request, 'Access denied. You can only view your own details.')
            return redirect('myapp:student_dashboard')
    
    context = {
        'student': student,
        'payments': Payment.objects.filter(student=student).order_by('-created_at'),
    }
    return render(request, 'myapp/student_detail.html', context)


# ============================================================================
# SCHOOL FEES MODULE - ROLE-BASED ACCESS
# ============================================================================

@login_required
def school_fees_home(request):
    """School fees home - different content for different roles"""
    if request.user.myapp_profile.role == 'admin':
        # Admin sees all students and fee structures
        students = Student.objects.all().order_by('-created_at')
        fee_structures = FeeStructure.objects.all().order_by('-created_at')
        context = {
            'students': students,
            'fee_structures': fee_structures,
            'view_type': 'admin'
        }
        return render(request, 'myapp/school_fees_admin.html', context)
    
    elif request.user.myapp_profile.role == 'student':
        # Student sees only their own payment options
        try:
            student = request.user.myapp_profile.student
            available_fees = FeeStructure.objects.filter(is_active=True)
            student_payments = Payment.objects.filter(student=student).order_by('-created_at')
            
            context = {
                'student': student,
                'available_fees': available_fees,
                'recent_payments': student_payments[:5],
                'view_type': 'student'
            }
            return render(request, 'myapp/school_fees_student.html', context)
        except:
            messages.error(request, 'Student profile not found.')
            return redirect('home')
    
    else:
        messages.error(request, 'Access denied.')
        return redirect('home')


# ============================================================================
# DONATION MODULE - ROLE-BASED ACCESS
# ============================================================================

@login_required
def donation_home(request):
    """Donation home - different access levels for different roles"""
    if request.user.myapp_profile.role == 'admin':
        # Admin sees all donation events and can manage them
        events = DonationEvent.objects.all().order_by('-created_at')
        context = {
            'events': events,
            'view_type': 'admin'
        }
        return render(request, 'myapp/donation_admin.html', context)
    
    elif request.user.myapp_profile.role == 'student':
        # Student sees only active donation events they can contribute to
        events = DonationEvent.objects.filter(is_active=True).order_by('-created_at')
        context = {
            'events': events,
            'view_type': 'student'
        }
        return render(request, 'myapp/donation_student.html', context)
    
    else:
        messages.error(request, 'Access denied.')
        return redirect('home')


# ============================================================================
# UTILITY VIEWS
# ============================================================================

@login_required
def profile_view(request):
    """User profile view - accessible by all authenticated users"""
    user = request.user
    try:
        profile = user.myapp_profile
        context = {
            'user': user,
            'profile': profile,
        }
        return render(request, 'myapp/profile.html', context)
    except:
        messages.error(request, 'Profile not found.')
        return redirect('home')


@login_required
def access_denied(request):
    """Access denied page"""
    return render(request, 'myapp/access_denied.html') 