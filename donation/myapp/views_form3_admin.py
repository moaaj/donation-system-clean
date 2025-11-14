"""
Form 3 Admin Views - Restricted to Form 3 students only
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO

from .models import (
    Student, FeeCategory, FeeStructure, Payment, PaymentReceipt, 
    Invoice, FeeDiscount, PaymentReminder, IndividualStudentFee, FeeStatus
)
from .forms import StudentForm, FeeStructureForm, IndividualStudentFeeForm
from accounts.decorators import form3_admin_required


@form3_admin_required
def form3_admin_dashboard(request):
    """Form 3 Admin Dashboard - Shows only Form 3 students and their data"""
    
    # Get only Form 3 students - handle both numeric and text formats
    form3_students = Student.objects.filter(
        level_custom__in=['3', 'Form 3'],
        is_active=True
    ).order_by('first_name', 'last_name')
    
    # Get Form 3 fee structures
    form3_fee_structures = FeeStructure.objects.filter(
        form__iexact='Form 3',
        is_active=True
    )
    
    # Get Form 3 payments
    form3_payments = Payment.objects.filter(
        student__in=form3_students
    ).order_by('-created_at')[:10]
    
    # Get Form 3 fee statuses
    form3_fee_statuses = FeeStatus.objects.filter(
        student__in=form3_students
    )
    
    # Calculate statistics for Form 3 only
    total_form3_students = form3_students.count()
    total_form3_payments = Payment.objects.filter(student__in=form3_students).count()
    total_form3_revenue = Payment.objects.filter(
        student__in=form3_students,
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Pending payments for Form 3 students (fees that are due but not paid)
    pending_payments = form3_fee_statuses.filter(
        status__in=['pending', 'overdue']
    ).count()
    
    # Completed payments for Form 3 students
    completed_payments = Payment.objects.filter(
        student__in=form3_students,
        status='completed'
    ).count()
    
    # Pending fees for Form 3 students
    pending_fees = form3_fee_statuses.filter(status__in=['pending', 'overdue']).count()
    
    # Recent Form 3 activities
    recent_payments = form3_payments[:5]
    recent_fee_statuses = form3_fee_statuses.order_by('-created_at')[:5]
    
    context = {
        'form3_students': form3_students,
        'form3_fee_structures': form3_fee_structures,
        'form3_payments': form3_payments,
        'form3_fee_statuses': form3_fee_statuses,
        'total_form3_students': total_form3_students,
        'total_form3_payments': total_form3_payments,
        'total_form3_revenue': total_form3_revenue,
        'pending_payments': pending_payments,
        'completed_payments': completed_payments,
        'pending_fees': pending_fees,
        'recent_payments': recent_payments,
        'recent_fee_statuses': recent_fee_statuses,
        'view_type': 'form3_admin',
    }
    
    return render(request, 'myapp/form3_admin_dashboard.html', context)


@form3_admin_required
def form3_student_list(request):
    """Form 3 Student List - Shows only Form 3 students"""
    
    show = request.GET.get('show', 'active')
    
    # Base queryset - only Form 3 students (handle both numeric and text formats)
    base_queryset = Student.objects.filter(
        level_custom__in=['3', 'Form 3']
    )
    
    # Filter based on show parameter
    if show == 'all':
        students = base_queryset
    else:
        students = base_queryset.filter(is_active=True)
    
    # Order by name
    students = students.order_by('first_name', 'last_name')
    
    context = {
        'students': students,
        'show': show,
        'view_type': 'form3_admin',
    }
    
    return render(request, 'myapp/form3_student_list.html', context)


@form3_admin_required
def form3_student_detail(request, id):
    """Form 3 Student Detail - Only accessible for Form 3 students"""
    
    # Get student and verify they are Form 3
    student = get_object_or_404(Student, id=id)
    
    if not (student.level_custom in ['3', 'Form 3']):
        messages.error(request, 'Access denied. This student is not in Form 3.')
        return redirect('form3_admin:student_list')
    
    # Get student's fee statuses
    fee_statuses = FeeStatus.objects.filter(student=student).select_related('fee_structure')
    
    # Get student's payments
    payments = Payment.objects.filter(student=student).order_by('-created_at')
    
    # Get student's individual fees (only unpaid ones)
    individual_fees = IndividualStudentFee.objects.filter(
        student=student,
        is_active=True,
        is_paid=False  # Filter out paid individual fees
    ).order_by('-created_at')
    
    # Get student's discounts
    discounts = FeeDiscount.objects.filter(student=student)
    
    context = {
        'student': student,
        'fee_statuses': fee_statuses,
        'payments': payments,
        'individual_fees': individual_fees,
        'discounts': discounts,
        'view_type': 'form3_admin',
    }
    
    return render(request, 'myapp/form3_student_detail.html', context)


@form3_admin_required
def form3_fee_management(request):
    """Form 3 Fee Management - Manage fees for Form 3 students only"""
    
    # Get Form 3 students first (handle both numeric and text formats)
    form3_students = Student.objects.filter(
        level_custom__in=['3', 'Form 3'],
        is_active=True
    )
    
    # Get Form 3 fee structures that have unpaid statuses
    # Only show fee structures that still have pending/overdue statuses
    unpaid_fee_structure_ids = FeeStatus.objects.filter(
        student__in=form3_students,
        status__in=['pending', 'overdue']
    ).values_list('fee_structure_id', flat=True).distinct()
    
    fee_structures = FeeStructure.objects.filter(
        id__in=unpaid_fee_structure_ids,
        form__iexact='Form 3',
        is_active=True
    ).select_related('category')
    
    # Get Form 3 fee statuses (only unpaid ones)
    fee_statuses = FeeStatus.objects.filter(
        student__in=form3_students,
        status__in=['pending', 'overdue']  # Filter out paid statuses
    ).select_related('student', 'fee_structure')
    
    context = {
        'fee_structures': fee_structures,
        'form3_students': form3_students,
        'fee_statuses': fee_statuses,
        'view_type': 'form3_admin',
    }
    
    return render(request, 'myapp/form3_fee_management.html', context)


@form3_admin_required
def form3_payment_management(request):
    """Form 3 Payment Management - Manage payments for Form 3 students only"""
    
    # Get Form 3 students (handle both numeric and text formats)
    form3_students = Student.objects.filter(
        level_custom__in=['3', 'Form 3'],
        is_active=True
    )
    
    # Get Form 3 payments
    payments = Payment.objects.filter(
        student__in=form3_students
    ).order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        payments = payments.filter(status=status_filter)
    
    # Filter by student if provided
    student_filter = request.GET.get('student')
    if student_filter:
        payments = payments.filter(student_id=student_filter)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        payments = payments.filter(
            Q(student__first_name__icontains=search_query) |
            Q(student__last_name__icontains=search_query) |
            Q(student__student_id__icontains=search_query) |
            Q(payment_id__icontains=search_query)
        )
    
    # Calculate statistics properly
    total_payments = payments.count()
    completed_payments_count = payments.filter(status='completed').count()
    pending_payments_count = payments.filter(status='pending').count()
    total_revenue = payments.filter(status='completed').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    context = {
        'payments': payments,
        'form3_students': form3_students,
        'status_filter': status_filter,
        'student_filter': student_filter,
        'search_query': search_query,
        'total_payments': total_payments,
        'completed_payments_count': completed_payments_count,
        'pending_payments_count': pending_payments_count,
        'total_revenue': total_revenue,
        'view_type': 'form3_admin',
    }
    
    return render(request, 'myapp/form3_payment_management.html', context)


@form3_admin_required
def form3_add_individual_fee(request):
    """Add individual fee for Form 3 students only"""
    
    if request.method == 'POST':
        form = IndividualStudentFeeForm(request.POST)
        if form.is_valid():
            individual_fee = form.save(commit=False)
            
            # Verify student is Form 3
            if not (individual_fee.student.level_custom in ['3', 'Form 3']):
                messages.error(request, 'Access denied. Can only add fees for Form 3 students.')
                return redirect('form3_admin:add_individual_fee')
            
            individual_fee.created_by = request.user
            individual_fee.save()
            messages.success(request, f'Individual fee added for {individual_fee.student.first_name} {individual_fee.student.last_name}')
            return redirect('form3_admin:student_detail', id=individual_fee.student.id)
    else:
        form = IndividualStudentFeeForm()
        # Filter students to only Form 3 (handle both numeric and text formats)
        form.fields['student'].queryset = Student.objects.filter(
            level_custom__in=['3', 'Form 3'],
            is_active=True
        )
    
    context = {
        'form': form,
        'view_type': 'form3_admin',
    }
    
    return render(request, 'myapp/form3_add_individual_fee.html', context)


@form3_admin_required
def form3_analytics(request):
    """Form 3 Analytics - Analytics for Form 3 students only"""
    
    try:
        # Get Form 3 students
        form3_students = Student.objects.filter(
            level='form',
            level_custom__iexact='Form 3',
            is_active=True
        )
        
        # Calculate analytics for Form 3 only
        total_students = form3_students.count()
        total_payments = Payment.objects.filter(student__in=form3_students).count()
        total_revenue = Payment.objects.filter(
            student__in=form3_students,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Payment status breakdown
        payment_statuses = Payment.objects.filter(student__in=form3_students).values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        # Fee status breakdown
        fee_statuses = FeeStatus.objects.filter(student__in=form3_students).values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        # Monthly revenue for Form 3
        monthly_revenue = []
        for i in range(12):
            month_start = date.today().replace(day=1) - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            
            month_revenue = Payment.objects.filter(
                student__in=form3_students,
                status='completed',
                created_at__date__range=[month_start, month_end]
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            monthly_revenue.append({
                'month': month_start.strftime('%b %Y'),
                'revenue': month_revenue
            })
        
        context = {
            'total_students': total_students,
            'total_payments': total_payments,
            'total_revenue': total_revenue,
            'payment_statuses': payment_statuses,
            'fee_statuses': fee_statuses,
            'monthly_revenue': monthly_revenue,
            'view_type': 'form3_admin',
        }
        
        return render(request, 'myapp/form3_analytics.html', context)
    
    except Exception as e:
        # If there's an error, return a simple error page
        context = {
            'error': str(e),
            'view_type': 'form3_admin',
        }
        return render(request, 'myapp/form3_analytics.html', context)


# ============================================================================
# ADDITIONAL FORM 3 ADMIN VIEWS - COMPLETE SCHOOL FEES CAPABILITIES
# ============================================================================

@form3_admin_required
def form3_fee_categories(request):
    """Form 3 Fee Categories Management"""
    
    # Get fee categories (all categories, not just Form 3 specific)
    categories = FeeCategory.objects.all().order_by('name')
    
    context = {
        'categories': categories,
        'view_type': 'form3_admin',
    }
    
    return render(request, 'myapp/form3_fee_categories.html', context)


@form3_admin_required
def form3_add_fee_category(request):
    """Add new fee category for Form 3 admin"""
    
    if request.method == 'POST':
        from .forms import FeeCategoryForm
        form = FeeCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fee category added successfully!')
            return redirect('form3_admin:fee_categories')
    else:
        from .forms import FeeCategoryForm
        form = FeeCategoryForm()
    
    context = {
        'form': form,
        'view_type': 'form3_admin',
    }
    
    return render(request, 'myapp/form3_add_fee_category.html', context)


@form3_admin_required
def form3_edit_fee_category(request, category_id):
    """Edit fee category for Form 3 admin"""
    
    category = get_object_or_404(FeeCategory, id=category_id)
    
    if request.method == 'POST':
        from .forms import FeeCategoryForm
        form = FeeCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fee category updated successfully!')
            return redirect('form3_admin:fee_categories')
    else:
        from .forms import FeeCategoryForm
        form = FeeCategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'view_type': 'form3_admin',
    }
    
    return render(request, 'myapp/form3_edit_fee_category.html', context)


@form3_admin_required
def form3_add_fee_structure(request):
    """Add new fee structure for Form 3 admin"""
    
    if request.method == 'POST':
        from .forms import FeeStructureForm
        form = FeeStructureForm(request.POST)
        if form.is_valid():
            fee_structure = form.save(commit=False)
            # Ensure it's for Form 3
            fee_structure.form = 'Form 3'
            fee_structure.save()
            messages.success(request, 'Fee structure added successfully!')
            return redirect('form3_admin:fee_management')
    else:
        from .forms import FeeStructureForm
        form = FeeStructureForm()
        # Pre-fill form as Form 3
        form.fields['form'].initial = 'Form 3'
    
    context = {
        'form': form,
        'view_type': 'form3_admin',
    }
    
    return render(request, 'myapp/form3_add_fee_structure.html', context)


@form3_admin_required
def form3_edit_fee_structure(request, structure_id):
    """Edit fee structure for Form 3 admin"""
    
    fee_structure = get_object_or_404(FeeStructure, id=structure_id)
    
    # Verify it's a Form 3 fee structure
    if fee_structure.form.lower() != 'form 3':
        messages.error(request, 'Access denied. This is not a Form 3 fee structure.')
        return redirect('form3_admin:fee_management')
    
    if request.method == 'POST':
        from .forms import FeeStructureForm
        form = FeeStructureForm(request.POST, instance=fee_structure)
        if form.is_valid():
            fee_structure = form.save(commit=False)
            # Ensure it remains Form 3
            fee_structure.form = 'Form 3'
            fee_structure.save()
            messages.success(request, 'Fee structure updated successfully!')
            return redirect('form3_admin:fee_management')
    else:
        from .forms import FeeStructureForm
        form = FeeStructureForm(instance=fee_structure)
    
    context = {
        'form': form,
        'fee_structure': fee_structure,
        'view_type': 'form3_admin',
    }
    
    return render(request, 'myapp/form3_edit_fee_structure.html', context)


@form3_admin_required
def form3_pending_fees(request):
    """Form 3 Pending Fees Management"""
    
    # Get Form 3 students (handle both numeric and text formats)
    form3_students = Student.objects.filter(
        level_custom__in=['3', 'Form 3'],
        is_active=True
    )
    
    # Get pending fee statuses for Form 3 students
    pending_fees = FeeStatus.objects.filter(
        student__in=form3_students,
        status__in=['pending', 'overdue']
    ).select_related('student', 'fee_structure')
    
    context = {
        'pending_fees': pending_fees,
        'form3_students': form3_students,
        'view_type': 'form3_admin',
    }
    
    return render(request, 'myapp/form3_pending_fees.html', context)


@form3_admin_required
def form3_add_fee_status(request):
    """Add fee status for Form 3 students"""
    
    if request.method == 'POST':
        from .forms import FeeStatusForm
        form = FeeStatusForm(request.POST)
        if form.is_valid():
            fee_status = form.save(commit=False)
            
            # Verify student is Form 3
            if not (fee_status.student.level_custom in ['3', 'Form 3']):
                messages.error(request, 'Access denied. Can only add fee status for Form 3 students.')
                return redirect('form3_admin:add_fee_status')
            
            fee_status.save()
            messages.success(request, f'Fee status added for {fee_status.student.first_name} {fee_status.student.last_name}')
            return redirect('form3_admin:pending_fees')
    else:
        from .forms import FeeStatusForm
        form = FeeStatusForm()
        # Filter students to only Form 3 (handle both numeric and text formats)
        form.fields['student'].queryset = Student.objects.filter(
            level_custom__in=['3', 'Form 3'],
            is_active=True
        )
    
    context = {
        'form': form,
        'view_type': 'form3_admin',
    }
    
    return render(request, 'myapp/form3_add_fee_status.html', context)


@form3_admin_required
def form3_fee_waivers(request):
    """Form 3 Fee Waivers Management"""
    
    # Get Form 3 students (handle both numeric and text formats)
    form3_students = Student.objects.filter(
        level_custom__in=['3', 'Form 3'],
        is_active=True
    )
    
    # Get fee waivers for Form 3 students
    from .models import FeeWaiver
    fee_waivers = FeeWaiver.objects.filter(
        student__in=form3_students
    ).select_related('student').order_by('-created_at')
    
    context = {
        'fee_waivers': fee_waivers,
        'form3_students': form3_students,
        'view_type': 'form3_admin',
    }
    
    return render(request, 'myapp/form3_fee_waivers.html', context)


@form3_admin_required
def form3_add_fee_waiver(request):
    """Add fee waiver for Form 3 students"""
    
    if request.method == 'POST':
        from .forms import FeeWaiverForm
        form = FeeWaiverForm(request.POST)
        if form.is_valid():
            fee_waiver = form.save(commit=False)
            
            # Verify student is Form 3
            if not (fee_waiver.student.level_custom in ['3', 'Form 3']):
                messages.error(request, 'Access denied. Can only add fee waivers for Form 3 students.')
                return redirect('form3_admin:add_fee_waiver')
            
            fee_waiver.save()
            messages.success(request, f'Fee waiver added for {fee_waiver.student.first_name} {fee_waiver.student.last_name}')
            return redirect('form3_admin:fee_waivers')
    else:
        from .forms import FeeWaiverForm
        form = FeeWaiverForm()
        # Filter students to only Form 3 (handle both numeric and text formats)
        form.fields['student'].queryset = Student.objects.filter(
            level_custom__in=['3', 'Form 3'],
            is_active=True
        )
    
    context = {
        'form': form,
        'view_type': 'form3_admin',
    }
    
    return render(request, 'myapp/form3_add_fee_waiver.html', context)


@form3_admin_required
def form3_fee_reports(request):
    """Form 3 Fee Reports"""
    
    # Get Form 3 students (handle both numeric and text formats)
    form3_students = Student.objects.filter(
        level_custom__in=['3', 'Form 3'],
        is_active=True
    )
    
    # Get fee statuses for Form 3 students
    fee_statuses = FeeStatus.objects.filter(
        student__in=form3_students
    ).select_related('student', 'fee_structure')
    
    # Get payments for Form 3 students
    payments = Payment.objects.filter(
        student__in=form3_students
    ).order_by('-created_at')
    
    context = {
        'fee_statuses': fee_statuses,
        'payments': payments,
        'form3_students': form3_students,
        'view_type': 'form3_admin',
    }
    
    return render(request, 'myapp/form3_fee_reports.html', context)


@form3_admin_required
def form3_export_fee_report(request):
    """Export Form 3 fee report"""
    
    # Get Form 3 students (handle both numeric and text formats)
    form3_students = Student.objects.filter(
        level_custom__in=['3', 'Form 3'],
        is_active=True
    )
    
    # Get fee statuses for Form 3 students
    fee_statuses = FeeStatus.objects.filter(
        student__in=form3_students
    ).select_related('student', 'fee_structure')
    
    # Create CSV response
    from django.http import HttpResponse
    import csv
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="form3_fee_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Student ID', 'Student Name', 'Fee Category', 'Amount', 'Status', 'Due Date'])
    
    for fee_status in fee_statuses:
        writer.writerow([
            fee_status.student.student_id,
            f"{fee_status.student.first_name} {fee_status.student.last_name}",
            fee_status.fee_structure.category.name,
            fee_status.amount,
            fee_status.get_status_display(),
            fee_status.due_date
        ])
    
    return response


@form3_admin_required
def form3_bank_accounts(request):
    """Form 3 Bank Accounts Management"""
    
    from .models import SchoolBankAccount
    bank_accounts = SchoolBankAccount.objects.all().order_by('bank_name')
    
    context = {
        'bank_accounts': bank_accounts,
        'view_type': 'form3_admin',
    }
    
    return render(request, 'myapp/form3_bank_accounts.html', context)


@form3_admin_required
def form3_add_bank_account(request):
    """Add bank account for Form 3 admin"""
    
    if request.method == 'POST':
        from .forms import SchoolBankAccountForm
        form = SchoolBankAccountForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bank account added successfully!')
            return redirect('form3_admin:bank_accounts')
    else:
        from .forms import SchoolBankAccountForm
        form = SchoolBankAccountForm()
    
    context = {
        'form': form,
        'view_type': 'form3_admin',
    }
    
    return render(request, 'myapp/form3_add_bank_account.html', context)


@form3_admin_required
def form3_payment_receipts(request):
    """Form 3 Payment Receipts"""
    
    # Get Form 3 students (handle both numeric and text formats)
    form3_students = Student.objects.filter(
        level_custom__in=['3', 'Form 3'],
        is_active=True
    )
    
    # Get payments for Form 3 students
    payments = Payment.objects.filter(
        student__in=form3_students,
        status='completed'
    ).order_by('-created_at')
    
    context = {
        'payments': payments,
        'view_type': 'form3_admin',
    }
    
    return render(request, 'myapp/form3_payment_receipts.html', context)


@form3_admin_required
def form3_payment_receipt(request, payment_id):
    """Form 3 Payment Receipt Detail"""
    
    payment = get_object_or_404(Payment, id=payment_id)
    
    # Verify student is Form 3
    if not (payment.student.level_custom in ['3', 'Form 3']):
        messages.error(request, 'Access denied. This payment is not for a Form 3 student.')
        return redirect('form3_admin:payment_receipts')
    
    context = {
        'payment': payment,
        'view_type': 'form3_admin',
    }
    
    return render(request, 'myapp/form3_payment_receipt.html', context)
