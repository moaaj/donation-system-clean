from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from accounts.decorators import admin_required, student_required, role_required, student_owns_payment, student_owns_student_record
from .models import Student, Payment, FeeStructure, FeeCategory, DonationEvent, Donation, FeeStatus
from .forms import PaymentForm, StudentForm, FeeStructureForm
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.http import FileResponse
from reportlab.pdfgen import canvas
from io import BytesIO
import csv
from django.http import HttpResponse


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
            # Only show fee structures that are due (FeeStatus is pending or overdue)
            due_statuses = FeeStatus.objects.filter(student=student, status__in=['pending', 'overdue'])
            due_fee_ids = due_statuses.values_list('fee_structure_id', flat=True)
            available_fees = FeeStructure.objects.filter(is_active=True, id__in=due_fee_ids)
            student_payments = Payment.objects.filter(student=student).order_by('-created_at')
            total_payments = Payment.objects.filter(student=student).count()
            # Special restriction for tamim123
            is_tamim = request.user.username == 'tamim123'
            # If tamim123 and no due statuses, available_fees should be empty
            if is_tamim and due_statuses.count() == 0:
                available_fees = FeeStructure.objects.none()
            context = {
                'student': student,
                'available_fees': available_fees,
                'recent_payments': student_payments[:5],
                'view_type': 'student',
                'is_tamim': is_tamim,
                'total_payments': total_payments,
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
    next_url = request.POST.get('next')
    cart = request.session.get('cart', [])
    if fee_id and fee_id not in cart:
        cart.append(fee_id)
        request.session['cart'] = cart
        messages.success(request, 'Fee added to cart.')
    else:
        messages.info(request, 'Fee already in cart or invalid.')
    if next_url:
        return redirect(next_url)
    return redirect('myapp:school_fees_home')

@student_required
def view_cart(request):
    cart = request.session.get('cart', [])
    fees = FeeStructure.objects.filter(id__in=cart)
    total = sum(fee.amount for fee in fees)
    return render(request, 'myapp/cart.html', {'fees': fees, 'total': total})

@student_required
@require_POST
def remove_from_cart(request):
    fee_id = request.POST.get('fee_id')
    cart = request.session.get('cart', [])
    if fee_id in cart:
        cart.remove(fee_id)
        request.session['cart'] = cart
        messages.success(request, 'Fee removed from cart.')
    else:
        messages.info(request, 'Fee not in cart.')
    return redirect('myapp:view_cart')

@student_required
def checkout_cart(request):
    student = request.user.myapp_profile.student
    cart = request.session.get('cart', [])
    fees = FeeStructure.objects.filter(id__in=cart)
    if not fees:
        messages.info(request, 'Your cart is empty.')
        return redirect('myapp:view_cart')
    payment_ids = []
    for fee in fees:
        if fee is not None:
            payment = Payment.objects.create(
                student=student,
                fee_structure=fee,
                amount=fee.amount,
                payment_date=timezone.now().date(),
                payment_method='online',
                status='completed'
            )
            # Mark the corresponding FeeStatus as paid
            FeeStatus.objects.filter(student=student, fee_structure=fee, status__in=['pending', 'overdue']).update(status='paid')
            payment_ids.append(payment.id)
    request.session['cart'] = []
    total_payments = Payment.objects.filter(student=student).count()
    request.session['total_payments'] = total_payments
    # Store the last payment IDs in session for receipt
    request.session['last_cart_payment_ids'] = payment_ids
    # Redirect to PDF receipt download
    return redirect('myapp:cart_receipt_pdf')

@student_required
def cart_receipt(request):
    payment_ids = request.session.get('last_cart_payment_ids', [])
    payments = Payment.objects.filter(id__in=payment_ids)
    student = request.user.myapp_profile.student
    return render(request, 'myapp/cart_receipt.html', {'payments': payments, 'student': student})

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
    p.drawString(100, y, "Fee Category")
    p.drawString(250, y, "Form")
    p.drawString(320, y, "Amount (RM)")
    p.drawString(420, y, "Date")
    p.setFont("Helvetica", 12)
    total = 0
    for payment in payments:
        y -= 25
        p.drawString(100, y, str(payment.fee_structure.category.name))
        p.drawString(250, y, str(payment.fee_structure.form))
        p.drawString(320, y, f"{payment.amount}")
        p.drawString(420, y, payment.payment_date.strftime('%Y-%m-%d'))
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
    response['Refresh'] = '0; url=/school-fees/'
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