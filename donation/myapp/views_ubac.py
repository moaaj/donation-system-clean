from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count
from accounts.decorators import admin_required, student_required, role_required, student_owns_payment, student_owns_student_record
from .models import Student, Payment, FeeStructure, FeeCategory, DonationEvent, Donation, FeeStatus, IndividualStudentFee
from .forms import PaymentForm, StudentForm, FeeStructureForm
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.http import FileResponse
from reportlab.pdfgen import canvas
from io import BytesIO
import csv
from django.http import HttpResponse
from .models import Invoice
from datetime import timedelta


# ============================================================================
# ADMIN-ONLY VIEWS
# ============================================================================

@admin_required
def admin_dashboard(request):
    """Admin dashboard - only accessible by admins"""
    from django.db.models import Sum, Count, Q
    
    # Calculate comprehensive statistics
    total_students = Student.objects.count()
    total_payments = Payment.objects.count()
    total_paid = Payment.objects.filter(status='completed').count()
    pending_payments = Payment.objects.filter(status='pending').count()
    overdue_payments = FeeStatus.objects.filter(status='overdue').count()
    total_revenue = Payment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Additional metrics
    active_students = Student.objects.filter(is_active=True).count()
    total_fee_structures = FeeStructure.objects.count()
    total_categories = FeeCategory.objects.count()
    
    # Calculate rates
    payment_rate = (total_paid / total_payments * 100) if total_payments > 0 else 0
    collection_rate = (total_revenue / (total_revenue + (Payment.objects.filter(status='pending').aggregate(Sum('amount'))['amount__sum'] or 0)) * 100) if total_revenue > 0 else 0
    
    # Recent activities (mock data for now)
    recent_activities = [
        {
            'icon': 'user-plus',
            'title': 'New Student Registered',
            'description': 'Student ID: STU2024001 was added to the system',
            'time': '2 hours ago'
        },
        {
            'icon': 'money-bill-wave',
            'title': 'Payment Completed',
            'description': 'RM 500.00 received for Tuition Fee',
            'time': '4 hours ago'
        },
        {
            'icon': 'cog',
            'title': 'Fee Structure Updated',
            'description': 'Monthly fee amount was modified',
            'time': '1 day ago'
        },
        {
            'icon': 'chart-line',
            'title': 'Report Generated',
            'description': 'Monthly payment report was exported',
            'time': '2 days ago'
        }
    ]
    
    context = {
        'total_students': total_students,
        'total_payments': total_payments,
        'total_paid': total_paid,
        'pending_payments': pending_payments,
        'overdue_payments': overdue_payments,
        'total_revenue': total_revenue,
        'active_students': active_students,
        'total_fee_structures': total_fee_structures,
        'total_categories': total_categories,
        'payment_rate': payment_rate,
        'collection_rate': collection_rate,
        'recent_activities': recent_activities,
        'recent_payments': Payment.objects.all().order_by('-created_at')[:5],
        'recent_students': Student.objects.all().order_by('-created_at')[:5],
    }
    return render(request, 'myapp/admin_dashboard.html', context)

@admin_required
def moaaj_dashboard(request):
    """Personalized dashboard for user Moaaj"""
    from django.db.models import Sum, Count, Q
    
    # Calculate comprehensive statistics
    total_students = Student.objects.count()
    total_payments = Payment.objects.count()
    total_paid = Payment.objects.filter(status='completed').count()
    pending_payments = Payment.objects.filter(status='pending').count()
    overdue_payments = FeeStatus.objects.filter(status='overdue').count()
    total_revenue = Payment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Additional metrics
    active_students = Student.objects.filter(is_active=True).count()
    total_fee_structures = FeeStructure.objects.count()
    total_categories = FeeCategory.objects.count()
    
    # Calculate rates
    payment_rate = (total_paid / total_payments * 100) if total_payments > 0 else 0
    collection_rate = (total_revenue / (total_revenue + (Payment.objects.filter(status='pending').aggregate(Sum('amount'))['amount__sum'] or 0)) * 100) if total_revenue > 0 else 0
    
    # Recent activities (mock data for now)
    recent_activities = [
        {
            'icon': 'user-plus',
            'title': 'New Student Registered',
            'description': 'Student ID: STU2024001 was added to the system',
            'time': '2 hours ago'
        },
        {
            'icon': 'money-bill-wave',
            'title': 'Payment Completed',
            'description': 'RM 500.00 received for Tuition Fee',
            'time': '4 hours ago'
        },
        {
            'icon': 'cog',
            'title': 'Fee Structure Updated',
            'description': 'Monthly fee amount was modified',
            'time': '1 day ago'
        },
        {
            'icon': 'chart-line',
            'title': 'Report Generated',
            'description': 'Monthly payment report was exported',
            'time': '2 days ago'
        }
    ]
    
    context = {
        'total_students': total_students,
        'total_payments': total_payments,
        'total_paid': total_paid,
        'pending_payments': pending_payments,
        'overdue_payments': overdue_payments,
        'total_revenue': total_revenue,
        'active_students': active_students,
        'total_fee_structures': total_fee_structures,
        'total_categories': total_categories,
        'payment_rate': payment_rate,
        'collection_rate': collection_rate,
        'recent_activities': recent_activities,
        'recent_payments': Payment.objects.all().order_by('-created_at')[:5],
        'recent_students': Student.objects.all().order_by('-created_at')[:5],
    }
    return render(request, 'myapp/moaaj_dashboard.html', context)


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
    """Comprehensive Payment Analytics Dashboard - only accessible by admins"""
    from django.db.models import Sum, Count, Q
    from django.utils import timezone
    from datetime import datetime, timedelta
    import json
    
    # Get filter parameters
    filter_type = request.GET.get('filter_type', 'all')  # all, student, class, batch, school, category
    filter_value = request.GET.get('filter_value', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    status_filter = request.GET.get('status', 'all')  # all, paid, pending
    
    # Base queryset
    payments = Payment.objects.all()
    fee_statuses = FeeStatus.objects.all()
    
    # Apply date filters
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            payments = payments.filter(payment_date__gte=date_from_obj)
            fee_statuses = fee_statuses.filter(due_date__gte=date_from_obj)
        except:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            payments = payments.filter(payment_date__lte=date_to_obj)
            fee_statuses = fee_statuses.filter(due_date__lte=date_to_obj)
        except:
            pass
    
    # Apply status filter
    if status_filter == 'paid':
        payments = payments.filter(status='completed')
        fee_statuses = fee_statuses.filter(status='paid')
    elif status_filter == 'pending':
        payments = payments.filter(status='pending')
        fee_statuses = fee_statuses.filter(status__in=['pending', 'overdue'])
    
    # Apply specific filters
    if filter_type == 'student' and filter_value:
        payments = payments.filter(student__first_name__icontains=filter_value) | payments.filter(student__last_name__icontains=filter_value)
        fee_statuses = fee_statuses.filter(student__first_name__icontains=filter_value) | fee_statuses.filter(student__last_name__icontains=filter_value)
    elif filter_type == 'class' and filter_value:
        payments = payments.filter(student__class_name__icontains=filter_value)
        fee_statuses = fee_statuses.filter(student__class_name__icontains=filter_value)
    elif filter_type == 'category' and filter_value:
        payments = payments.filter(fee_structure__category__name__icontains=filter_value)
        fee_statuses = fee_statuses.filter(fee_structure__category__name__icontains=filter_value)
    
    # Calculate analytics data
    total_payments = payments.count()
    total_paid = payments.filter(status='completed').count()
    total_pending = payments.filter(status='pending').count()
    total_amount_paid = payments.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
    total_amount_pending = payments.filter(status='pending').aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Fee Status analytics
    total_fee_statuses = fee_statuses.count()
    paid_fee_statuses = fee_statuses.filter(status='paid').count()
    pending_fee_statuses = fee_statuses.filter(status='pending').count()
    overdue_fee_statuses = fee_statuses.filter(status='overdue').count()
    
    # Get unique values for filters
    students = Student.objects.all().order_by('first_name')
    classes = Student.objects.values_list('class_name', flat=True).distinct().exclude(class_name__isnull=True).exclude(class_name='')
    categories = FeeCategory.objects.all().order_by('name')
    
    # Chart data for payments by category
    payments_by_category = payments.filter(status='completed').values('fee_structure__category__name').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    category_chart_data = {
        'labels': [item['fee_structure__category__name'] or 'Individual Fee' for item in payments_by_category],
        'data': [float(item['total']) for item in payments_by_category],
        'counts': [item['count'] for item in payments_by_category]
    }
    
    # Chart data for payments by class
    payments_by_class = payments.filter(status='completed').values('student__class_name').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    class_chart_data = {
        'labels': [item['student__class_name'] or 'No Class' for item in payments_by_class],
        'data': [float(item['total']) for item in payments_by_class],
        'counts': [item['count'] for item in payments_by_class]
    }
    
    # Monthly payment trends (last 12 months)
    monthly_data = []
    for i in range(12):
        month_date = timezone.now().date() - timedelta(days=30*i)
        month_start = month_date.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        month_payments = payments.filter(
            payment_date__gte=month_start,
            payment_date__lte=month_end,
            status='completed'
        )
        
        monthly_data.append({
            'month': month_start.strftime('%b %Y'),
            'amount': float(month_payments.aggregate(Sum('amount'))['amount__sum'] or 0),
            'count': month_payments.count()
        })
    
    monthly_chart_data = {
        'labels': [item['month'] for item in reversed(monthly_data)],
        'amounts': [item['amount'] for item in reversed(monthly_data)],
        'counts': [item['count'] for item in reversed(monthly_data)]
    }
    
    # Status distribution
    status_distribution = {
        'paid': total_paid,
        'pending': total_pending,
        'overdue': overdue_fee_statuses
    }
    
    # Recent payments for table
    recent_payments = payments.order_by('-payment_date')[:20]
    
    # Export functionality
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="payment_analytics_{timezone.now().strftime("%Y%m%d")}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Student', 'Class', 'Fee Category', 'Amount', 'Status', 'Payment Date'])
        for payment in payments:
            writer.writerow([
                f"{payment.student.first_name} {payment.student.last_name}",
                payment.student.class_name or 'N/A',
                payment.fee_structure.category.name if payment.fee_structure else 'Individual Fee',
                payment.amount,
                payment.status,
                payment.payment_date
            ])
        return response
    
    context = {
        # Summary statistics
        'total_payments': total_payments,
        'total_paid': total_paid,
        'total_pending': total_pending,
        'total_amount_paid': total_amount_paid,
        'total_amount_pending': total_amount_pending,
        'paid_fee_statuses': paid_fee_statuses,
        'pending_fee_statuses': pending_fee_statuses,
        'overdue_fee_statuses': overdue_fee_statuses,
        
        # Filter options
        'students': students,
        'classes': classes,
        'categories': categories,
        'filter_type': filter_type,
        'filter_value': filter_value,
        'date_from': date_from,
        'date_to': date_to,
        'status_filter': status_filter,
        
        # Chart data
        'category_chart_data': json.dumps(category_chart_data),
        'class_chart_data': json.dumps(class_chart_data),
        'monthly_chart_data': json.dumps(monthly_chart_data),
        'status_distribution': json.dumps(status_distribution),
        
        # Table data
        'recent_payments': recent_payments,
        'payments_by_category': payments_by_category,
        'payments_by_class': payments_by_class,
        
        # Additional analytics
        'payment_rate': (total_paid / total_payments * 100) if total_payments > 0 else 0,
        'collection_rate': (total_amount_paid / (total_amount_paid + total_amount_pending) * 100) if (total_amount_paid + total_amount_pending) > 0 else 0,
    }
    
    return render(request, 'myapp/payment_analytics.html', context)


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
        # Filters
        category = request.GET.get('category')
        status = request.GET.get('status')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        if category:
            payments = payments.filter(fee_structure__category__name__icontains=category)
        if status:
            payments = payments.filter(status=status)
        if date_from:
            payments = payments.filter(payment_date__gte=date_from)
        if date_to:
            payments = payments.filter(payment_date__lte=date_to)
        categories = FeeCategory.objects.all()
        # Export CSV
        if request.GET.get('export') == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="payment_history.csv"'
            writer = csv.writer(response)
            writer.writerow(['Fee Category', 'Form', 'Amount (RM)', 'Date', 'Status'])
            for payment in payments:
                writer.writerow([
                    payment.fee_structure.category.name,
                    payment.fee_structure.form,
                    payment.amount,
                    payment.payment_date,
                    payment.status
                ])
            return response
        context = {
            'payments': payments,
            'student': student,
            'categories': categories,
            'selected_category': category or '',
            'selected_status': status or '',
            'date_from': date_from or '',
            'date_to': date_to or '',
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
    print("DEBUG: school_fees_home view called!")
    print(f"DEBUG: Request URL: {request.path}")
    print(f"DEBUG: User: {request.user.username}")
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
        try:
            student = request.user.myapp_profile.student
            # Get all fee statuses for this student to show payment status
            fee_statuses = FeeStatus.objects.filter(student=student).select_related('fee_structure')
            print(f"DEBUG: Student {student.first_name} has {len(fee_statuses)} fee statuses")
            print(f"DEBUG: Fee statuses: {[(fs.fee_structure.category.name, fs.status) for fs in fee_statuses[:3]]}")
            
            # Force refresh from database
            from django.db import connection
            connection.close()
            fee_statuses = FeeStatus.objects.filter(student=student).select_related('fee_structure')
            print(f"DEBUG: After refresh - Fee statuses: {[(fs.fee_structure.category.name, fs.status) for fs in fee_statuses[:3]]}")
            
            # Show all active fee structures for students
            # If a fee has FeeStatus records, only show if any are pending/overdue
            # If a fee has no FeeStatus records, show it (it's new and needs to be assigned)
            all_active_fees = FeeStructure.objects.filter(is_active=True)
            
            # Get fees that have pending/overdue status
            pending_fee_ids = fee_statuses.filter(status__in=['pending', 'overdue']).values_list('fee_structure_id', flat=True)
            
            # Get fees that have no FeeStatus records (new fees)
            fees_with_status = fee_statuses.values_list('fee_structure_id', flat=True)
            new_fees = all_active_fees.exclude(id__in=fees_with_status)
            
            # Get fees that are completely paid (all FeeStatus records are 'paid')
            paid_fee_ids = []
            for fee in all_active_fees:
                fee_statuses_for_fee = fee_statuses.filter(fee_structure=fee)
                if fee_statuses_for_fee.exists() and fee_statuses_for_fee.exclude(status='paid').count() == 0:
                    # All FeeStatus records for this fee are 'paid'
                    paid_fee_ids.append(fee.id)
            
            # Combine pending fees and new fees, but exclude completely paid fees
            available_fees = all_active_fees.filter(
                id__in=list(pending_fee_ids) + list(new_fees.values_list('id', flat=True))
            ).exclude(id__in=paid_fee_ids)
            student_payments = Payment.objects.filter(student=student).order_by('-created_at')
            total_payments = Payment.objects.filter(student=student).count()
            
            # Get individual student fees for this student (only unpaid fees)
            individual_fees = []
            try:
                individual_fees = IndividualStudentFee.objects.filter(
                    student=student, 
                    is_active=True,
                    is_paid=False  # Only show unpaid fees
                ).select_related('category').order_by('-created_at')
            except:
                individual_fees = []
            
            # Special restriction for tamim123
            is_tamim = request.user.username == 'tamim123'
            # If tamim123 and no due statuses, available_fees should be empty
            if is_tamim and due_statuses.count() == 0:
                available_fees = FeeStructure.objects.none()
            
            context = {
                'student': student,
                'available_fees': available_fees,
                'fee_statuses': fee_statuses,  # Add fee statuses list
                'recent_payments': student_payments[:5],
                'view_type': 'student',
                'is_tamim': is_tamim,
                'total_payments': total_payments,
                'individual_fees': individual_fees,  # Add individual fees to context
            }
            return render(request, 'myapp/school_fees_student.html', context)
        except Exception as e:
            messages.error(request, f'Student profile not found. {e}')
            return redirect('home')
    
    else:
        messages.error(request, 'Access denied.')
        return redirect('home')

@student_required
@require_POST
def add_to_cart(request):
    fee_id = request.POST.get('fee_id')
    individual_fee_id = request.POST.get('individual_fee_id')
    next_url = request.POST.get('next')
    
    # Initialize cart structure if not exists
    if 'cart' not in request.session:
        request.session['cart'] = {'fees': [], 'individual_fees': []}
    
    cart = request.session['cart']
    
    # Migrate old cart format to new format if needed
    if isinstance(cart, list):
        # Old format was a list of fee IDs
        old_cart = cart
        cart = {'fees': old_cart, 'individual_fees': []}
        request.session['cart'] = cart
    
    if fee_id:
        # Handle regular fee structure
        if fee_id not in cart['fees']:
            cart['fees'].append(fee_id)
            request.session['cart'] = cart
            messages.success(request, 'Fee added to cart.')
        else:
            messages.info(request, 'Fee already in cart.')
    
    elif individual_fee_id:
        # Handle individual student fee
        if individual_fee_id not in cart['individual_fees']:
            cart['individual_fees'].append(individual_fee_id)
            request.session['cart'] = cart
            messages.success(request, 'Individual fee added to cart.')
        else:
            messages.info(request, 'Individual fee already in cart.')
    
    else:
        messages.error(request, 'No fee selected.')
    
    if next_url:
        return redirect(next_url)
    return redirect('myapp:school_fees_home')

@student_required
def view_cart(request):
    print("DEBUG: view_cart function called!")
    cart = request.session.get('cart', {'fees': [], 'individual_fees': []})
    print(f"DEBUG: Cart in session: {cart}")
    
    # Migrate old cart format to new format if needed
    if isinstance(cart, list):
        # Old format was a list of fee IDs
        old_cart = cart
        cart = {'fees': old_cart, 'individual_fees': []}
        request.session['cart'] = cart
    
    # Get regular fees
    regular_fees = FeeStructure.objects.filter(id__in=cart.get('fees', []))
    print(f"DEBUG: Found {regular_fees.count()} regular fees in cart")
    
    # Get individual fees
    individual_fees = IndividualStudentFee.objects.filter(id__in=cart.get('individual_fees', []))
    print(f"DEBUG: Found {individual_fees.count()} individual fees in cart")
    
    # Calculate totals
    regular_total = sum(fee.amount for fee in regular_fees)
    individual_total = sum(fee.amount for fee in individual_fees)
    total = regular_total + individual_total
    
    context = {
        'regular_fees': regular_fees,
        'individual_fees': individual_fees,
        'total': total,
        'regular_total': regular_total,
        'individual_total': individual_total
    }
    return render(request, 'myapp/cart.html', context)

@student_required
@require_POST
def remove_from_cart(request):
    fee_id = request.POST.get('fee_id')
    individual_fee_id = request.POST.get('individual_fee_id')
    cart = request.session.get('cart', {'fees': [], 'individual_fees': []})
    
    # Migrate old cart format to new format if needed
    if isinstance(cart, list):
        # Old format was a list of fee IDs
        old_cart = cart
        cart = {'fees': old_cart, 'individual_fees': []}
        request.session['cart'] = cart
    
    if fee_id and fee_id in cart.get('fees', []):
        cart['fees'].remove(fee_id)
        request.session['cart'] = cart
        messages.success(request, 'Fee removed from cart.')
    elif individual_fee_id and individual_fee_id in cart.get('individual_fees', []):
        cart['individual_fees'].remove(individual_fee_id)
        request.session['cart'] = cart
        messages.success(request, 'Individual fee removed from cart.')
    else:
        messages.info(request, 'Fee not in cart.')
    
    return redirect('myapp:view_cart')

@student_required
def checkout_cart(request):
    print("=" * 50)
    print("DEBUG: checkout_cart function called!")
    print(f"DEBUG: Request method: {request.method}")
    print(f"DEBUG: User: {request.user.username}")
    print(f"DEBUG: Request path: {request.path}")
    print(f"DEBUG: Request URL: {request.build_absolute_uri()}")
    print(f"DEBUG: User is authenticated: {request.user.is_authenticated}")
    print(f"DEBUG: User has myapp_profile: {hasattr(request.user, 'myapp_profile')}")
    if hasattr(request.user, 'myapp_profile'):
        print(f"DEBUG: User role: {request.user.myapp_profile.role}")
    print("=" * 50)
    
    # Only process if it's a POST request
    if request.method != 'POST':
        print("DEBUG: Not a POST request, redirecting to cart")
        return redirect('myapp:view_cart')
    
    student = request.user.myapp_profile.student
    cart = request.session.get('cart', {'fees': [], 'individual_fees': []})
    print(f"DEBUG: Cart contents: {cart}")
    print(f"DEBUG: Student: {student.first_name if student else 'None'}")
    
    # Migrate old cart format to new format if needed
    if isinstance(cart, list):
        # Old format was a list of fee IDs
        old_cart = cart
        cart = {'fees': old_cart, 'individual_fees': []}
        request.session['cart'] = cart
    
    # Get regular fees
    regular_fees = FeeStructure.objects.filter(id__in=cart.get('fees', []))
    
    # Get individual fees
    individual_fees = IndividualStudentFee.objects.filter(id__in=cart.get('individual_fees', []))
    
    if not regular_fees and not individual_fees:
        print("DEBUG: Cart is empty - no fees found")
        messages.info(request, 'Your cart is empty.')
        return redirect('myapp:view_cart')
    else:
        print(f"DEBUG: Found {regular_fees.count()} regular fees and {individual_fees.count()} individual fees")
    
    payment_ids = []
    
    # Process regular fees
    for fee in regular_fees:
        if fee is not None:
            print(f"DEBUG: Processing fee {fee.id} - {fee.category.name}")
            
            # Create payment record
            payment = Payment.objects.create(
                student=student,
                fee_structure=fee,
                amount=fee.amount,
                payment_date=timezone.now().date(),
                payment_method='online',
                status='completed'
            )
            print(f"DEBUG: Created payment {payment.id} for fee {fee.id}")
            
            # Handle FeeStatus updates
            if fee.frequency == 'monthly':
                # For monthly fees, update all pending FeeStatus records
                fee_statuses = FeeStatus.objects.filter(
                    student=student,
                    fee_structure=fee,
                    status__in=['pending', 'overdue']
                )
                print(f"DEBUG: Found {fee_statuses.count()} pending FeeStatus records for monthly fee")
                if fee_statuses.exists():
                    fee_statuses.update(status='paid')
                    print(f"DEBUG: Updated all pending FeeStatus records to paid")
                else:
                    # Create FeeStatus records for monthly fees if they don't exist
                    print(f"DEBUG: No FeeStatus records found for monthly fee, creating them manually")
                    
                    # Create monthly FeeStatus records manually
                    monthly_amount = fee.get_monthly_amount()
                    from datetime import timedelta
                    start_date = timezone.now().date()
                    
                    for month in range(fee.monthly_duration):
                        due_date = start_date + timedelta(days=30 * month)
                        
                        # Create FeeStatus record
                        fee_status = FeeStatus.objects.create(
                            student=student,
                            fee_structure=fee,
                            amount=monthly_amount,
                            due_date=due_date,
                            status='paid'  # Mark as paid immediately
                        )
                        print(f"DEBUG: Created FeeStatus record {fee_status.id} for month {month + 1}")
                    
                    print(f"DEBUG: Created {fee.monthly_duration} FeeStatus records for monthly fee")
            else:
                # For non-monthly fees, always create or update FeeStatus
                fee_status, created = FeeStatus.objects.get_or_create(
                    student=student,
                    fee_structure=fee,
                    defaults={
                        'amount': fee.amount,
                        'due_date': timezone.now().date(),
                        'status': 'paid'
                    }
                )
                if not created:
                    # Update existing FeeStatus to paid
                    print(f"DEBUG: Updating existing FeeStatus {fee_status.id} from {fee_status.status} to paid")
                    fee_status.status = 'paid'
                    fee_status.save()
                else:
                    print(f"DEBUG: Created new FeeStatus {fee_status.id} with status paid")
            
            # Get the final status for debugging
            if fee.frequency == 'monthly':
                final_statuses = FeeStatus.objects.filter(student=student, fee_structure=fee)
                print(f"DEBUG: Final FeeStatus records for monthly fee: {[fs.status for fs in final_statuses]}")
            else:
                final_status = FeeStatus.objects.filter(student=student, fee_structure=fee).first()
                print(f"DEBUG: Final FeeStatus status: {final_status.status if final_status else 'None'}")
            
            payment_ids.append(payment.id)
    
    # Process individual fees
    for individual_fee in individual_fees:
        if individual_fee is not None:
            # Create payment for individual fee
            payment = Payment.objects.create(
                student=student,
                fee_structure=None,  # Individual fees don't have fee_structure
                amount=individual_fee.amount,
                payment_date=timezone.now().date(),
                payment_method='online',
                status='completed'
            )
            # Mark the individual fee as paid
            individual_fee.is_paid = True
            individual_fee.save()
            payment_ids.append(payment.id)
    
    print("DEBUG: Finished processing regular fees")
    
    print("DEBUG: About to clear cart...")
    # Clear cart
    print(f"DEBUG: Clearing cart. Before: {request.session.get('cart')}")
    request.session['cart'] = {'fees': [], 'individual_fees': []}
    request.session.modified = True  # Force session save
    print(f"DEBUG: Cart cleared. After: {request.session.get('cart')}")
    print(f"DEBUG: Session modified flag: {request.session.modified}")
    
    # Force save the session
    request.session.save()
    print(f"DEBUG: Session saved. Cart after save: {request.session.get('cart')}")
    
    # Force database refresh
    from django.db import connection
    connection.close()
    print("DEBUG: Database connection closed to force refresh")
    
    total_payments = Payment.objects.filter(student=student).count()
    request.session['total_payments'] = total_payments
    # Store the last payment IDs in session for receipt and invoice
    request.session['last_cart_payment_ids'] = payment_ids
    print(f"DEBUG: Stored payment_ids in session: {payment_ids}")
    print(f"DEBUG: Session cart_payment_ids after store: {request.session.get('last_cart_payment_ids')}")
    
    # Add success message
    messages.success(request, f'Payment completed successfully! {len(payment_ids)} item(s) paid. Invoice generated.')
    
    # Instead of redirecting, render the invoice page directly
    print("DEBUG: Rendering invoice page directly")
    
    # Generate invoices for each payment
    from datetime import timedelta
    invoices = []
    for payment_id in payment_ids:
        payment = Payment.objects.get(id=payment_id)
        invoice, created = Invoice.objects.get_or_create(
            payment=payment,
            defaults={
                'student': student,
                'amount': payment.amount,
                'due_date': timezone.now().date() + timedelta(days=30),
                'status': 'sent',
                'notes': f'Invoice for {payment.fee_structure.category.name if payment.fee_structure else "Individual Fee"}',
                'terms_conditions': 'Payment is due within 30 days of invoice date.'
            }
        )
        invoices.append(invoice)
    
    print(f"DEBUG: Generated {len(invoices)} invoices")
    print("DEBUG: Rendering invoice page directly")
    
    # Generate invoices for each payment
    from datetime import timedelta
    invoices = []
    for payment_id in payment_ids:
        payment = Payment.objects.get(id=payment_id)
        invoice, created = Invoice.objects.get_or_create(
            payment=payment,
            defaults={
                'student': student,
                'amount': payment.amount,
                'due_date': timezone.now().date() + timedelta(days=30),
                'status': 'sent',
                'notes': f'Invoice for {payment.fee_structure.category.name if payment.fee_structure else "Individual Fee"}',
                'terms_conditions': 'Payment is due within 30 days of invoice date.'
            }
        )
        invoices.append(invoice)
    
    print(f"DEBUG: Generated {len(invoices)} invoices")
    print("DEBUG: Rendering beautiful invoice page directly")
    
    # Create beautiful invoice HTML directly
    from django.http import HttpResponse
    total_amount = sum(invoice.total_amount for invoice in invoices)
    
    invoice_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Payment Invoice</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            body {{
                background-color: #f8f9fa;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }}
            .success-header {{
                background: linear-gradient(135deg, #28a745, #20c997);
                border-radius: 15px;
                color: white;
                padding: 2rem;
                margin-bottom: 2rem;
            }}
            .invoice-card {{
                background: white;
                border-radius: 15px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-bottom: 1.5rem;
                border: 1px solid #e9ecef;
            }}
            .invoice-header {{
                background: white;
                border-bottom: 2px solid #f8f9fa;
                border-radius: 15px 15px 0 0;
                padding: 1.5rem;
            }}
            .total-summary {{
                background: linear-gradient(135deg, #f8f9fa, #e9ecef);
                border-radius: 15px;
                padding: 2rem;
                text-align: center;
            }}
            .action-btn {{
                border-radius: 10px;
                padding: 0.75rem 1.5rem;
                font-weight: 500;
            }}
            .bg-opacity-20 {{
                background-color: rgba(255, 255, 255, 0.2) !important;
            }}
        </style>
    </head>
    <body>
        <div class="container mt-4">
            <!-- Success Message -->
            <div class="alert alert-success alert-dismissible fade show" role="alert">
                <i class="fas fa-check-circle"></i> Payment completed successfully! {len(invoices)} item(s) paid. Invoice generated.
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>

            <!-- Thank You Section -->
            <div class="success-header text-center">
                <div class="mb-3">
                    <i class="fas fa-file-invoice" style="font-size: 3rem; color: rgba(255,255,255,0.9);"></i>
                </div>
                <h2 class="mb-3"><strong>Payment Invoice Generated!</strong></h2>
                <p class="mb-4">Your payment has been successfully processed and an invoice has been generated.</p>
                <div class="row justify-content-center">
                    <div class="col-md-3">
                        <div class="bg-opacity-20 rounded p-3">
                            <h4 class="mb-1">{len(invoices)}</h4>
                            <small>Invoice(s) Generated</small>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="bg-opacity-20 rounded p-3">
                            <h4 class="mb-1">RM {total_amount}</h4>
                            <small>Total Amount</small>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Invoice Details -->
    """
    
    # Add each invoice
    for i, invoice in enumerate(invoices):
        invoice_html += f"""
            <div class="invoice-card">
                <div class="invoice-header">
                    <div class="d-flex justify-content-between align-items-center">
                        <h5 class="mb-0">
                            <i class="fas fa-receipt text-primary me-2"></i>
                            Invoice #{invoice.invoice_number}
                        </h5>
                        <span class="badge bg-success px-3 py-2">{invoice.get_status_display()}</span>
                    </div>
                </div>
                <div class="card-body">
                    <!-- Student Information -->
                    <div class="row mb-4">
                        <div class="col-md-6">
                            <h6 class="text-muted mb-2">STUDENT INFORMATION</h6>
                            <p class="mb-1"><strong>{student.first_name} {student.last_name}</strong></p>
                            <p class="mb-1 text-muted">Student ID: {student.student_id}</p>
                            <p class="mb-0 text-muted">Class: {getattr(student, 'class_name', 'Not specified')}</p>
                        </div>
                        <div class="col-md-6 text-md-end">
                            <h6 class="text-muted mb-2">INVOICE DETAILS</h6>
                            <p class="mb-1"><strong>Issue Date:</strong> {invoice.issue_date}</p>
                            <p class="mb-1"><strong>Due Date:</strong> {invoice.due_date}</p>
                            <p class="mb-0"><strong>Status:</strong> {invoice.get_status_display()}</p>
                        </div>
                    </div>

                    <!-- Payment Details -->
                    <div class="bg-light rounded p-4 mb-4">
                        <h6 class="text-muted mb-3">PAYMENT DETAILS</h6>
                        <div class="row">
                            <div class="col-md-8">
                                <p class="mb-2">
                                    <strong>
                                        {invoice.payment.fee_structure.category.name if invoice.payment.fee_structure else "Individual Student Fee"}
                                        {f" - {invoice.payment.fee_structure.form}" if invoice.payment.fee_structure else ""}
                                    </strong>
                                </p>
                                <small class="text-muted">
                                    {invoice.payment.fee_structure.get_frequency_display() if invoice.payment.fee_structure else "One-time"} Payment
                                </small>
                            </div>
                            <div class="col-md-4 text-end">
                                <p class="mb-1"><strong>Amount:</strong> RM {invoice.amount}</p>
                                <p class="mb-1"><strong>Tax (6%):</strong> RM {invoice.tax_amount}</p>
                                <p class="mb-0"><strong>Total:</strong> RM {invoice.total_amount}</p>
                            </div>
                        </div>
                    </div>

                    <!-- Notes and Terms -->
                    {f'<div class="mb-3"><h6 class="text-muted mb-2">NOTES</h6><p class="mb-0">{invoice.notes}</p></div>' if invoice.notes else ''}
                    {f'<div class="mb-3"><h6 class="text-muted mb-2">TERMS & CONDITIONS</h6><p class="mb-0">{invoice.terms_conditions}</p></div>' if invoice.terms_conditions else ''}
                </div>
            </div>
        """
    
    # Add total summary and action buttons
    invoice_html += f"""
            <!-- Total Summary -->
            <div class="total-summary">
                <h4 class="mb-2">Total Amount Due</h4>
                <h2 class="text-primary mb-0">RM {total_amount}</h2>
            </div>

            <!-- Action Buttons -->
            <div class="row justify-content-center mb-5">
                <div class="col-md-8">
                    <div class="row g-3">
                        <div class="col-md-6">
                            <a href="/school-fees/student/cart-invoice-pdf/" class="btn btn-primary w-100 action-btn">
                                <i class="fas fa-download me-2"></i>
                                Download PDF Invoice
                            </a>
                        </div>
                        <div class="col-md-6">
                            <a href="/school-fees/student/cart-receipt/" class="btn btn-success w-100 action-btn">
                                <i class="fas fa-receipt me-2"></i>
                                View Receipt
                            </a>
                        </div>
                        <div class="col-md-6">
                            <a href="/school-fees/" class="btn btn-outline-secondary w-100 action-btn">
                                <i class="fas fa-arrow-left me-2"></i>
                                Back to School Fees
                            </a>
                        </div>
                        <div class="col-md-6">
                            <a href="/school-fees/student/payments/" class="btn btn-outline-info w-100 action-btn">
                                <i class="fas fa-history me-2"></i>
                                Payment History
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    
    return HttpResponse(invoice_html)

@student_required
def cart_receipt(request):
    payment_ids = request.session.get('last_cart_payment_ids', [])
    payments = Payment.objects.filter(id__in=payment_ids)
    student = request.user.myapp_profile.student
    
    # If no payment IDs in session, show a message
    if not payment_ids:
        messages.warning(request, 'No recent payments found. Please complete a payment first.')
        return redirect('myapp:school_fees_home')
    
    # Create beautiful receipt HTML directly
    from django.http import HttpResponse
    total_amount = sum(float(payment.amount) for payment in payments)
    
    receipt_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Payment Receipt</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            body {{
                background-color: #f8f9fa;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }}
            .success-header {{
                background: linear-gradient(135deg, #28a745, #20c997);
                border-radius: 15px;
                color: white;
                padding: 2rem;
                margin-bottom: 2rem;
            }}
            .receipt-card {{
                background: white;
                border-radius: 15px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-bottom: 1.5rem;
                border: 1px solid #e9ecef;
            }}
            .receipt-header {{
                background: white;
                border-bottom: 2px solid #f8f9fa;
                border-radius: 15px 15px 0 0;
                padding: 1.5rem;
            }}
            .total-summary {{
                background: linear-gradient(135deg, #f8f9fa, #e9ecef);
                border-radius: 15px;
                padding: 2rem;
                text-align: center;
            }}
            .action-btn {{
                border-radius: 10px;
                padding: 0.75rem 1.5rem;
                font-weight: 500;
            }}
            .bg-opacity-20 {{
                background-color: rgba(255, 255, 255, 0.2) !important;
            }}
            .receipt-item {{
                border-bottom: 1px solid #f8f9fa;
                padding: 1rem 0;
            }}
            .receipt-item:last-child {{
                border-bottom: none;
            }}
        </style>
    </head>
    <body>
        <div class="container mt-4">
            <!-- Success Message -->
            <div class="alert alert-success alert-dismissible fade show" role="alert">
                <i class="fas fa-check-circle"></i> Payment receipt generated successfully!
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>

            <!-- Thank You Section -->
            <div class="success-header text-center">
                <div class="mb-3">
                    <i class="fas fa-receipt" style="font-size: 3rem; color: rgba(255,255,255,0.9);"></i>
                </div>
                <h2 class="mb-3"><strong>Payment Receipt</strong></h2>
                <p class="mb-4">Your payment has been successfully processed. Here's your receipt.</p>
                <div class="row justify-content-center">
                    <div class="col-md-3">
                        <div class="bg-opacity-20 rounded p-3">
                            <h4 class="mb-1">{payments.count()}</h4>
                            <small>Payment(s) Made</small>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="bg-opacity-20 rounded p-3">
                            <h4 class="mb-1">RM {total_amount:.2f}</h4>
                            <small>Total Amount</small>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Receipt Details -->
            <div class="receipt-card">
                <div class="receipt-header">
                    <div class="d-flex justify-content-between align-items-center">
                        <h5 class="mb-0">
                            <i class="fas fa-receipt text-success me-2"></i>
                            Payment Receipt
                        </h5>
                        <span class="badge bg-success px-3 py-2">PAID</span>
                    </div>
                </div>
                <div class="card-body">
                    <!-- Student Information -->
                    <div class="row mb-4">
                        <div class="col-md-6">
                            <h6 class="text-muted mb-2">STUDENT INFORMATION</h6>
                            <p class="mb-1"><strong>{student.first_name} {student.last_name}</strong></p>
                            <p class="mb-1 text-muted">Student ID: {student.student_id}</p>
                            <p class="mb-0 text-muted">Class: {getattr(student, 'class_name', 'Not specified')}</p>
                        </div>
                        <div class="col-md-6 text-md-end">
                            <h6 class="text-muted mb-2">RECEIPT DETAILS</h6>
                            <p class="mb-1"><strong>Receipt Date:</strong> {timezone.now().strftime('%d %B %Y')}</p>
                            <p class="mb-1"><strong>Receipt Time:</strong> {timezone.now().strftime('%I:%M %p')}</p>
                            <p class="mb-0"><strong>Status:</strong> <span class="badge bg-success">PAID</span></p>
                        </div>
                    </div>

                    <!-- Payment Items -->
                    <div class="bg-light rounded p-4 mb-4">
                        <h6 class="text-muted mb-3">PAYMENT ITEMS</h6>
    """
    
    # Add each payment item
    for i, payment in enumerate(payments):
        if payment.fee_structure:
            fee_type = payment.fee_structure.category.name
            description = f"{payment.fee_structure.form} - {payment.fee_structure.get_frequency_display()}"
        else:
            # Individual fee
            individual_fee = IndividualStudentFee.objects.filter(
                student=student, 
                amount=payment.amount,
                is_paid=True
            ).first()
            if individual_fee:
                fee_type = individual_fee.category.name
                description = individual_fee.name
            else:
                fee_type = "Individual Fee"
                description = "Individual Student Fee"
        
        receipt_html += f"""
                        <div class="receipt-item">
                            <div class="row align-items-center">
                                <div class="col-md-6">
                                    <h6 class="mb-1">{fee_type}</h6>
                                    <p class="text-muted mb-0">{description}</p>
                                    <small class="text-muted">Payment Method: {payment.payment_method.title()}</small>
                                </div>
                                <div class="col-md-3 text-center">
                                    <span class="badge bg-success">PAID</span>
                                </div>
                                <div class="col-md-3 text-end">
                                    <h6 class="mb-0">RM {payment.amount}</h6>
                                    <small class="text-muted">{payment.payment_date.strftime('%d %b %Y')}</small>
                                </div>
                            </div>
                        </div>
        """
    
    # Add total summary and action buttons
    receipt_html += f"""
                    </div>
                </div>
            </div>

            <!-- Total Summary -->
            <div class="total-summary">
                <h4 class="mb-2">Total Amount Paid</h4>
                <h2 class="text-success mb-0">RM {total_amount:.2f}</h2>
            </div>

            <!-- Action Buttons -->
            <div class="row justify-content-center mb-5">
                <div class="col-md-8">
                    <div class="row g-3">
                        <div class="col-md-6">
                            <a href="/school-fees/student/cart-receipt-pdf/" class="btn btn-primary w-100 action-btn">
                                <i class="fas fa-download me-2"></i>
                                Download PDF Receipt
                            </a>
                        </div>
                        <div class="col-md-6">
                            <a href="/school-fees/student/cart-invoice/" class="btn btn-info w-100 action-btn">
                                <i class="fas fa-file-invoice me-2"></i>
                                View Invoice
                            </a>
                        </div>
                        <div class="col-md-6">
                            <a href="/school-fees/" class="btn btn-outline-secondary w-100 action-btn">
                                <i class="fas fa-arrow-left me-2"></i>
                                Back to School Fees
                            </a>
                        </div>
                        <div class="col-md-6">
                            <a href="/school-fees/student/payments/" class="btn btn-outline-info w-100 action-btn">
                                <i class="fas fa-history me-2"></i>
                                Payment History
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    
    return HttpResponse(receipt_html)

@student_required
def cart_receipt_pdf(request):
    payment_ids = request.session.get('last_cart_payment_ids', [])
    payments = Payment.objects.filter(id__in=payment_ids)
    student = request.user.myapp_profile.student
    # Generate PDF
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 800, "Payment Receipt")
    p.setFont("Helvetica", 12)
    p.drawString(100, 780, f"Student: {student.first_name} {student.last_name} ({student.student_id})")
    y = 750
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, y, "Fee Type")
    p.drawString(200, y, "Description")
    p.drawString(350, y, "Amount (RM)")
    p.drawString(450, y, "Date")
    p.setFont("Helvetica", 12)
    total = 0
    for payment in payments:
        y -= 25
        if payment.fee_structure:
            # Regular fee
            fee_type = payment.fee_structure.category.name
            description = f"{payment.fee_structure.form} - {payment.fee_structure.get_frequency_display()}"
        else:
            # Individual fee - we need to find the corresponding individual fee
            individual_fee = IndividualStudentFee.objects.filter(
                student=student, 
                amount=payment.amount,
                is_paid=True
            ).first()
            if individual_fee:
                fee_type = individual_fee.category.name
                description = individual_fee.name
            else:
                fee_type = "Individual Fee"
                description = "Individual Student Fee"
        
        p.drawString(100, y, str(fee_type))
        p.drawString(200, y, str(description))
        p.drawString(350, y, f"{payment.amount}")
        p.drawString(450, y, payment.payment_date.strftime('%Y-%m-%d'))
        total += float(payment.amount)
    y -= 30
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, y, f"Total Paid: RM {total}")
    p.showPage()
    p.save()
    buffer.seek(0)
    response = FileResponse(buffer, as_attachment=True, filename='payment_receipt.pdf')
    response['Content-Disposition'] += '; filename="payment_receipt.pdf"'
    # Add a Refresh header to redirect after download
    response['Refresh'] = '0; url=/student/cart-invoice/'
    return response

@student_required
def cart_invoice(request):
    print("DEBUG: cart_invoice function called!")
    print(f"DEBUG: Request method: {request.method}")
    print(f"DEBUG: Request path: {request.path}")
    print(f"DEBUG: User: {request.user.username}")
    
    payment_ids = request.session.get('last_cart_payment_ids', [])
    print(f"DEBUG: payment_ids from session: {payment_ids}")
    
    # If no payment IDs in session, show a message
    if not payment_ids:
        print("DEBUG: No payment IDs found, redirecting to school fees")
        messages.warning(request, 'No recent payments found. Please complete a payment first.')
        return redirect('myapp:school_fees_home')
    
    payments = Payment.objects.filter(id__in=payment_ids)
    print(f"DEBUG: found {payments.count()} payments")
    student = request.user.myapp_profile.student
    print(f"DEBUG: student: {student}")
    
    # Generate invoices for each payment
    from datetime import timedelta
    invoices = []
    for payment in payments:
        # Check if invoice already exists
        invoice, created = Invoice.objects.get_or_create(
            payment=payment,
            defaults={
                'student': student,
                'amount': payment.amount,
                'due_date': timezone.now().date() + timedelta(days=30),  # 30 days from now
                'status': 'sent',
                'notes': f'Invoice for {payment.fee_structure.category.name if payment.fee_structure else "Individual Fee"}',
                'terms_conditions': 'Payment is due within 30 days of invoice date.'
            }
        )
        invoices.append(invoice)
    
    print(f"DEBUG: Generated {len(invoices)} invoices")
    print(f"DEBUG: Rendering cart_invoice.html template")
    return render(request, 'myapp/cart_invoice.html', {'invoices': invoices, 'student': student})

@student_required
def cart_invoice_pdf(request):
    payment_ids = request.session.get('last_cart_payment_ids', [])
    payments = Payment.objects.filter(id__in=payment_ids)
    student = request.user.myapp_profile.student
    
    # Generate PDF
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 800, "INVOICE")
    p.setFont("Helvetica", 12)
    p.drawString(100, 780, f"Student: {student.first_name} {student.last_name} ({student.student_id})")
    p.drawString(100, 760, f"Date: {timezone.now().strftime('%Y-%m-%d')}")
    
    y = 720
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, y, "Description")
    p.drawString(300, y, "Amount (RM)")
    p.drawString(400, y, "Tax (RM)")
    p.drawString(500, y, "Total (RM)")
    p.setFont("Helvetica", 12)
    
    total_amount = 0
    total_tax = 0
    total_total = 0
    
    for payment in payments:
        y -= 25
        if payment.fee_structure:
            description = f"{payment.fee_structure.category.name} - {payment.fee_structure.form}"
        else:
            description = "Individual Student Fee"
        
        amount = float(payment.amount)
        tax = amount * 0.06  # 6% tax
        total = amount + tax
        
        p.drawString(100, y, description)
        p.drawString(300, y, f"{amount:.2f}")
        p.drawString(400, y, f"{tax:.2f}")
        p.drawString(500, y, f"{total:.2f}")
        
        total_amount += amount
        total_tax += tax
        total_total += total
    
    y -= 30
    p.setFont("Helvetica-Bold", 12)
    p.drawString(300, y, f"{total_amount:.2f}")
    p.drawString(400, y, f"{total_tax:.2f}")
    p.drawString(500, y, f"{total_total:.2f}")
    
    y -= 50
    p.setFont("Helvetica", 10)
    p.drawString(100, y, "Terms: Payment is due within 30 days of invoice date.")
    p.drawString(100, y-20, "Thank you for your business!")
    
    p.showPage()
    p.save()
    buffer.seek(0)
    response = FileResponse(buffer, as_attachment=True, filename='invoice.pdf')
    response['Content-Disposition'] += '; filename="invoice.pdf"'
    # Add a Refresh header to redirect after download
    response['Refresh'] = '0; url=/student/cart-invoice/'
    return response


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