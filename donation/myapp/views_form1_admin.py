"""
Form 1 Admin Views - Restricted to Form 1 students only
STRICT DATA ISOLATION: Only Form 1 data is accessible
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.http import JsonResponse
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from .models import (
    Student, FeeCategory, FeeStructure, Payment, PaymentReceipt, 
    Invoice, FeeDiscount, PaymentReminder, IndividualStudentFee, FeeStatus
)
from .forms import StudentForm, FeeStructureForm, IndividualStudentFeeForm
from accounts.decorators import form1_admin_required

# ============================================================================
# FORM 1 ADMIN CORE VIEWS - STRICT DATA ISOLATION
# ============================================================================

@form1_admin_required
def form1_admin_dashboard(request):
    """Form 1 Admin Dashboard - Accurate data for Form 1 students only"""
    
    # Initialize context with safe defaults
    context = {
        'total_students': 0,
        'total_payments': 0,
        'total_revenue': 0,
        'pending_payments': 0,
        'overdue_payments': 0,
        'monthly_revenue': 0,
        'form1_students': [],
        'form1_fee_structures': [],
        'form1_fee_categories': [],
        'recent_payments': [],
        'pending_fees': [],
        'payment_methods': [],
        'top_paying_students': [],
        'view_type': 'form1_admin',
    }
    
    try:
        # STRICT FILTERING: Only Form 1 students
        form1_students = Student.objects.filter(
            level='form',
            level_custom__iexact='Form 1',
            is_active=True
        )
        
        # Basic statistics
        total_students = form1_students.count()
        
        if total_students > 0:
            # STRICT FILTERING: Only Form 1 fee structures
            form1_fee_structures = FeeStructure.objects.filter(
                form__iexact='Form 1',
                is_active=True
            )
            
            # STRICT FILTERING: Only Form 1 payments
            form1_payments = Payment.objects.filter(student__in=form1_students)
            completed_payments = form1_payments.filter(status='completed')
            
            # STRICT FILTERING: Only Form 1 fee statuses
            form1_fee_statuses = FeeStatus.objects.filter(student__in=form1_students)
            
            # Calculate accurate statistics
            total_payments = form1_payments.count()
            total_revenue = completed_payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            # Pending and overdue payments
            pending_payments = form1_fee_statuses.filter(
                status__in=['pending', 'overdue']
            ).count()
            overdue_payments = form1_fee_statuses.filter(status='overdue').count()
            
            # Monthly revenue (current month)
            from datetime import datetime
            current_month = datetime.now().month
            current_year = datetime.now().year
            monthly_revenue = completed_payments.filter(
                created_at__month=current_month,
                created_at__year=current_year
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            # Recent payments (last 10)
            recent_payments = completed_payments.order_by('-created_at')[:10]
            
            # Pending fees (last 10)
            pending_fees = form1_fee_statuses.filter(
                status__in=['pending', 'overdue']
            ).select_related('student', 'fee_structure').order_by('-created_at')[:10]
            
            # Fee categories for Form 1
            form1_fee_categories = FeeCategory.objects.filter(
                feestructure__form__iexact='Form 1'
            ).distinct()
            
            # Payment methods breakdown
            payment_methods = form1_payments.values('payment_method').annotate(
                count=Count('id'),
                total=Sum('amount')
            ).order_by('-count')
            
            # Top paying Form 1 students
            top_paying_students = form1_students.annotate(
                total_paid=Sum('payment__amount', filter=Q(payment__status='completed'))
            ).filter(total_paid__gt=0).order_by('-total_paid')[:5]
            
            # Update context with accurate data
            context.update({
                'total_students': total_students,
                'total_payments': total_payments,
                'total_revenue': total_revenue,
                'pending_payments': pending_payments,
                'overdue_payments': overdue_payments,
                'monthly_revenue': monthly_revenue,
                'form1_students': form1_students[:10],
                'form1_fee_structures': form1_fee_structures[:10],
                'form1_fee_categories': form1_fee_categories,
                'recent_payments': recent_payments,
                'pending_fees': pending_fees,
                'payment_methods': payment_methods,
                'top_paying_students': top_paying_students,
            })
        
    except Exception as e:
        # Log error but don't cause redirect loop
        print(f"Error in Form 1 admin dashboard: {str(e)}")
        pass
    
    return render(request, 'myapp/form1_admin_dashboard_simple.html', context)


@form1_admin_required
def form1_student_list(request):
    """Form 1 Student List - Accurate data for Form 1 students only"""
    
    # STRICT FILTERING: Only Form 1 students
    form1_students = Student.objects.filter(
        level='form',
        level_custom__iexact='Form 1',
        is_active=True
    ).order_by('first_name', 'last_name')
    
    # Search functionality (within Form 1 students only)
    search_query = request.GET.get('search', '')
    if search_query:
        form1_students = form1_students.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(student_id__icontains=search_query) |
            Q(nric__icontains=search_query)
        )
    
    # Add payment and fee information for each student
    students_with_data = []
    for student in form1_students:
        # Get student's payments
        student_payments = Payment.objects.filter(student=student)
        total_paid = student_payments.filter(status='completed').aggregate(
            total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Get student's fee statuses
        student_fees = FeeStatus.objects.filter(student=student)
        pending_fees = student_fees.filter(status__in=['pending', 'overdue']).count()
        overdue_fees = student_fees.filter(status='overdue').count()
        
        # Get last payment
        last_payment = student_payments.filter(status='completed').order_by('-created_at').first()
        
        students_with_data.append({
            'student': student,
            'total_paid': total_paid,
            'pending_fees': pending_fees,
            'overdue_fees': overdue_fees,
            'last_payment': last_payment,
            'total_payments': student_payments.count(),
        })
    
    # Statistics
    total_students = form1_students.count()
    students_with_payments = sum(1 for s in students_with_data if s['total_paid'] > 0)
    students_with_pending = sum(1 for s in students_with_data if s['pending_fees'] > 0)
    students_overdue = sum(1 for s in students_with_data if s['overdue_fees'] > 0)
    
    context = {
        'students_with_data': students_with_data,
        'search_query': search_query,
        'total_students': total_students,
        'students_with_payments': students_with_payments,
        'students_with_pending': students_with_pending,
        'students_overdue': students_overdue,
        'view_type': 'form1_admin',
    }
    
    return render(request, 'myapp/form1_admin_dashboard_simple.html', context)


@form1_admin_required
def form1_student_detail(request, id):
    """Form 1 Student Detail - View individual Form 1 student details ONLY"""
    
    # STRICT FILTERING: Only Form 1 student
    student = get_object_or_404(
        Student, 
        id=id,
        level='form',
        level_custom__iexact='Form 1',
        is_active=True
    )
    
    # Get student's payments (already filtered by student)
    payments = Payment.objects.filter(student=student).order_by('-created_at')
    
    # Get student's fee statuses (already filtered by student)
    fee_statuses = FeeStatus.objects.filter(student=student).select_related('fee_structure')
    
    # Get student's individual fees (already filtered by student)
    individual_fees = IndividualStudentFee.objects.filter(student=student)
    
    # Calculate total amounts for this Form 1 student only
    total_paid = payments.filter(status='completed').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_pending = fee_statuses.filter(status__in=['pending', 'overdue']).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    context = {
        'student': student,
        'payments': payments,
        'fee_statuses': fee_statuses,
        'individual_fees': individual_fees,
        'total_paid': total_paid,
        'total_pending': total_pending,
        'view_type': 'form1_admin',
    }
    
    return render(request, 'myapp/form1_admin_dashboard_simple.html', context)


# ============================================================================
# FORM 1 ADMIN FEE MANAGEMENT - STRICT DATA ISOLATION
# ============================================================================

@form1_admin_required
def form1_fee_management(request):
    """Form 1 Fee Management - Accurate data for Form 1 fees only"""
    
    # STRICT FILTERING: Only Form 1 fee structures
    form1_fee_structures = FeeStructure.objects.filter(
        form__iexact='Form 1',
        is_active=True
    ).order_by('category__name', 'name')
    
    # STRICT FILTERING: Only Form 1 individual fees
    form1_individual_fees = IndividualStudentFee.objects.filter(
        student__level='form',
        student__level_custom__iexact='Form 1',
        student__is_active=True
    ).select_related('student', 'fee_structure').order_by('-created_at')
    
    # Fee categories for Form 1
    form1_fee_categories = FeeCategory.objects.filter(
        feestructure__form__iexact='Form 1'
    ).distinct()
    
    # Fee statistics
    total_fee_structures = form1_fee_structures.count()
    total_individual_fees = form1_individual_fees.count()
    
    # Calculate total revenue from fees
    total_fee_revenue = form1_individual_fees.aggregate(
        total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Fee status breakdown
    fee_status_breakdown = form1_individual_fees.values('status').annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('-count')
    
    # Fee structure statistics
    fee_structure_stats = []
    for structure in form1_fee_structures:
        structure_fees = form1_individual_fees.filter(fee_structure=structure)
        structure_revenue = structure_fees.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        structure_count = structure_fees.count()
        
        fee_structure_stats.append({
            'structure': structure,
            'revenue': structure_revenue,
            'count': structure_count,
        })
    
    context = {
        'form1_fee_structures': form1_fee_structures,
        'form1_individual_fees': form1_individual_fees,
        'form1_fee_categories': form1_fee_categories,
        'total_fee_structures': total_fee_structures,
        'total_individual_fees': total_individual_fees,
        'total_fee_revenue': total_fee_revenue,
        'fee_status_breakdown': fee_status_breakdown,
        'fee_structure_stats': fee_structure_stats,
        'view_type': 'form1_admin',
    }
    
    return render(request, 'myapp/form1_admin_dashboard_simple.html', context)


@form1_admin_required
def form1_add_individual_fee(request):
    """Add Individual Fee for Form 1 Student ONLY"""
    
    if request.method == 'POST':
        form = IndividualStudentFeeForm(request.POST)
        if form.is_valid():
            individual_fee = form.save(commit=False)
            
            # STRICT VALIDATION: Ensure only Form 1 students can be selected
            if individual_fee.student.level != 'form' or individual_fee.student.level_custom.lower() != 'form 1':
                messages.error(request, 'You can only add fees for Form 1 students.')
                return redirect('form1_admin:add_individual_fee')
            
            individual_fee.save()
            messages.success(request, f'Individual fee added for {individual_fee.student.first_name} {individual_fee.student.last_name}')
            return redirect('form1_admin:fee_management')
    else:
        form = IndividualStudentFeeForm()
        
        # STRICT FILTERING: Only Form 1 students in dropdown
        form.fields['student'].queryset = Student.objects.filter(
            level='form',
            level_custom__iexact='Form 1',
            is_active=True
        ).order_by('first_name', 'last_name')
    
    context = {
        'form': form,
        'view_type': 'form1_admin',
    }
    
    return render(request, 'myapp/form1_admin_dashboard_simple.html', context)


@form1_admin_required
def form1_add_fee_structure(request):
    """Add Fee Structure for Form 1 ONLY"""
    
    if request.method == 'POST':
        form = FeeStructureForm(request.POST)
        if form.is_valid():
            fee_structure = form.save(commit=False)
            fee_structure.form = 'Form 1'  # Force Form 1
            fee_structure.save()
            messages.success(request, f'Fee structure "{fee_structure.name}" added for Form 1')
            return redirect('form1_admin:fee_management')
    else:
        form = FeeStructureForm()
        # Set default form to Form 1
        form.initial['form'] = 'Form 1'
    
    context = {
        'form': form,
        'view_type': 'form1_admin',
    }
    
    return render(request, 'myapp/form1_admin_dashboard_simple.html', context)


@form1_admin_required
def form1_edit_fee_structure(request, structure_id):
    """Edit Fee Structure for Form 1 ONLY"""
    
    # STRICT FILTERING: Only Form 1 fee structure
    fee_structure = get_object_or_404(
        FeeStructure,
        id=structure_id,
        form__iexact='Form 1'
    )
    
    if request.method == 'POST':
        form = FeeStructureForm(request.POST, instance=fee_structure)
        if form.is_valid():
            form.save()
            messages.success(request, f'Fee structure "{fee_structure.name}" updated')
            return redirect('form1_admin:fee_management')
    else:
        form = FeeStructureForm(instance=fee_structure)
    
    context = {
        'form': form,
        'fee_structure': fee_structure,
        'view_type': 'form1_admin',
    }
    
    return render(request, 'myapp/form1_admin_dashboard_simple.html', context)


# ============================================================================
# FORM 1 ADMIN PAYMENT MANAGEMENT - STRICT DATA ISOLATION
# ============================================================================

@form1_admin_required
def form1_payment_management(request):
    """Form 1 Payment Management - View and manage payments for Form 1 students ONLY"""
    
    # STRICT FILTERING: Only Form 1 students
    form1_students = Student.objects.filter(
        level='form',
        level_custom__iexact='Form 1',
        is_active=True
    )
    
    # STRICT FILTERING: Only Form 1 payments
    form1_payments = Payment.objects.filter(
        student__in=form1_students
    ).select_related('student').order_by('-created_at')
    
    # Filter by status if requested
    status_filter = request.GET.get('status', '')
    if status_filter:
        form1_payments = form1_payments.filter(status=status_filter)
    
    # Search functionality (within Form 1 students only)
    search_query = request.GET.get('search', '')
    if search_query:
        form1_payments = form1_payments.filter(
            Q(student__first_name__icontains=search_query) |
            Q(student__last_name__icontains=search_query) |
            Q(student__student_id__icontains=search_query) |
            Q(reference_number__icontains=search_query)
        )
    
    # Calculate comprehensive statistics for Form 1 students only
    total_payments = form1_payments.count()
    completed_payments = form1_payments.filter(status='completed')
    pending_payments = form1_payments.filter(status='pending')
    failed_payments = form1_payments.filter(status='failed')
    
    total_revenue = completed_payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    pending_revenue = pending_payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Payment method breakdown
    payment_methods = form1_payments.values('payment_method').annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('-count')
    
    # Monthly revenue trend (last 6 months)
    from datetime import datetime, timedelta
    monthly_revenue = []
    for i in range(6):  # Last 6 months
        month_date = datetime.now() - timedelta(days=30*i)
        month_revenue = completed_payments.filter(
            created_at__month=month_date.month,
            created_at__year=month_date.year
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        monthly_revenue.append({
            'month': month_date.strftime('%b %Y'),
            'revenue': month_revenue
        })
    
    # Top paying students
    top_paying_students = form1_students.annotate(
        total_paid=Sum('payment__amount', filter=Q(payment__status='completed'))
    ).order_by('-total_paid')[:5]
    
    context = {
        'form1_payments': form1_payments,
        'total_payments': total_payments,
        'completed_payments': completed_payments.count(),
        'pending_payments': pending_payments.count(),
        'failed_payments': failed_payments.count(),
        'total_revenue': total_revenue,
        'pending_revenue': pending_revenue,
        'payment_methods': payment_methods,
        'monthly_revenue': monthly_revenue,
        'top_paying_students': top_paying_students,
        'status_filter': status_filter,
        'search_query': search_query,
        'view_type': 'form1_admin',
    }
    
    return render(request, 'myapp/form1_admin_dashboard_simple.html', context)


@form1_admin_required
def form1_payment_receipts(request):
    """Form 1 Payment Receipts - View payment receipts for Form 1 students ONLY"""
    
    # STRICT FILTERING: Only Form 1 students
    form1_students = Student.objects.filter(
        level='form',
        level_custom__iexact='Form 1',
        is_active=True
    )
    
    # STRICT FILTERING: Only payment receipts for Form 1 students
    receipts = PaymentReceipt.objects.filter(
        payment__student__in=form1_students
    ).select_related('payment', 'payment__student').order_by('-created_at')
    
    context = {
        'receipts': receipts,
        'view_type': 'form1_admin',
    }
    
    return render(request, 'myapp/form1_admin_dashboard_simple.html', context)


@form1_admin_required
def form1_payment_receipt(request, payment_id):
    """Form 1 Payment Receipt Detail - View specific payment receipt for Form 1 student ONLY"""
    
    # STRICT FILTERING: Only payment for Form 1 student
    payment = get_object_or_404(
        Payment,
        id=payment_id,
        student__level='form',
        student__level_custom__iexact='Form 1',
        student__is_active=True
    )
    
    # Get or create receipt
    receipt, created = PaymentReceipt.objects.get_or_create(
        payment=payment,
        defaults={
            'receipt_number': f"RCP-{payment.id}-{timezone.now().strftime('%Y%m%d')}",
            'issued_date': timezone.now().date()
        }
    )
    
    context = {
        'payment': payment,
        'receipt': receipt,
        'view_type': 'form1_admin',
    }
    
    return render(request, 'myapp/form1_admin_dashboard_simple.html', context)


# ============================================================================
# FORM 1 ADMIN ANALYTICS - STRICT DATA ISOLATION
# ============================================================================

@form1_admin_required
def form1_analytics(request):
    """Form 1 Analytics - Analytics dashboard for Form 1 students ONLY"""
    
    # STRICT FILTERING: Only Form 1 students
    form1_students = Student.objects.filter(
        level='form',
        level_custom__iexact='Form 1',
        is_active=True
    )
    
    # STRICT FILTERING: Only Form 1 payments
    form1_payments = Payment.objects.filter(student__in=form1_students)
    completed_payments = form1_payments.filter(status='completed')
    
    # Calculate statistics for Form 1 students only
    total_students = form1_students.count()
    total_revenue = completed_payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    average_payment = total_revenue / total_students if total_students > 0 else Decimal('0.00')
    
    # Payment status breakdown for Form 1 students only
    payment_stats = {
        'completed': form1_payments.filter(status='completed').count(),
        'pending': form1_payments.filter(status='pending').count(),
        'failed': form1_payments.filter(status='failed').count(),
        'cancelled': form1_payments.filter(status='cancelled').count(),
    }
    
    # Monthly revenue for Form 1 students only (last 6 months)
    monthly_revenue = []
    for i in range(6):
        month_start = (timezone.now().replace(day=1) - timedelta(days=i*30)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        revenue = completed_payments.filter(
            created_at__date__range=[month_start, month_end]
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        monthly_revenue.append({
            'month': month_start.strftime('%B %Y'),
            'revenue': revenue
        })
    
    monthly_revenue.reverse()
    
    context = {
        'total_students': total_students,
        'total_revenue': total_revenue,
        'average_payment': average_payment,
        'payment_stats': payment_stats,
        'monthly_revenue': monthly_revenue,
        'view_type': 'form1_admin',
    }
    
    return render(request, 'myapp/form1_admin_dashboard_simple.html', context)
