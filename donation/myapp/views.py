from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets
from .models import (
    Student, Parent, FeeCategory, FeeStructure, Payment,
    PaymentReceipt, FeeDiscount, PaymentReminder, SchoolBankAccount,
    DonationCategory, DonationEvent, Donation, EmailPreferences, FeeStatus,
    FeeWaiver, FeeSettings, AcademicTerm, IndividualStudentFee
)
from .serializers import PaymentSerializer
import requests
import hashlib
import json
from django.conf import settings
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.contrib import messages
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncMonth
from django.http import JsonResponse, HttpResponse
from .forms import (
    StudentForm, ParentForm, FeeCategoryForm, FeeStructureForm,
    PaymentForm, FeeDiscountForm, SchoolBankAccountForm, PaymentSearchForm,
    DonationCategoryForm, DonationEventForm, DonationForm, FeeWaiverForm,
    IndividualStudentFeeForm
)
from django.core.files.storage import default_storage
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.template.loader import get_template, render_to_string
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime, timezone
from django.utils import timezone
from django.core.mail import send_mail
from django.utils.html import strip_tags
from openpyxl import Workbook, load_workbook
import pandas as pd
from .ai_services import PaymentPredictionService
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import re

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

class SystemChatbot:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
        # Define system knowledge base
        self.knowledge_base = {
            'payment': {
                'keywords': ['payment', 'pay', 'fee', 'fees', 'amount', 'money', 'transaction'],
                'info': {
                    'how_to_pay': 'You can make payments through multiple methods: cash, bank transfer, or online payment.',
                    'payment_methods': 'Available payment methods are: cash, bank transfer, and online payment.',
                    'payment_status': 'Payment status can be: pending, completed, or failed.',
                    'receipt': 'After successful payment, you can download or email your receipt.',
                }
            },
            'student': {
                'keywords': ['student', 'students', 'enrollment', 'enroll', 'register', 'registration'],
                'info': {
                    'registration': 'Students can be registered through the student registration form.',
                    'profile': 'Student profiles include: name, ID, year batch, and active status.',
                    'fees': 'Each student is assigned fee structures based on their form and category.',
                }
            },
            'fee_structure': {
                'keywords': ['fee structure', 'fee category', 'categories', 'structure', 'pricing'],
                'info': {
                    'categories': 'Fee categories include: tuition, examination, and miscellaneous fees.',
                    'frequency': 'Fees can be collected monthly, termly, or yearly.',
                    'amount': 'Fee amounts vary based on the category and form level.',
                }
            },
            'discount': {
                'keywords': ['discount', 'discounts', 'waiver', 'waivers', 'scholarship', 'scholarships'],
                'info': {
                    'types': 'Available discounts: percentage-based, fixed amount, or full waiver.',
                    'eligibility': 'Discounts are based on merit, need, or special circumstances.',
                    'application': 'Discount applications can be submitted through the fee waiver form.',
                }
            },
            'report': {
                'keywords': ['report', 'reports', 'statement', 'statements', 'analytics', 'dashboard'],
                'info': {
                    'types': 'Available reports: payment reports, fee analytics, and collection reports.',
                    'access': 'Reports can be accessed through the dashboard or reports section.',
                    'export': 'Reports can be exported in PDF or Excel format.',
                }
            }
        }

    def preprocess_text(self, text):
        # Convert to lowercase
        text = text.lower()
        # Remove special characters
        text = re.sub(r'[^\w\s]', '', text)
        # Tokenize
        tokens = word_tokenize(text)
        # Remove stopwords and lemmatize
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens if token not in self.stop_words]
        return tokens

    def find_relevant_category(self, tokens):
        max_matches = 0
        best_category = None
        
        for category, data in self.knowledge_base.items():
            matches = sum(1 for token in tokens if token in data['keywords'])
            if matches > max_matches:
                max_matches = matches
                best_category = category
                
        return best_category

    def get_response(self, query):
        # Preprocess the query
        tokens = self.preprocess_text(query)
        
        # Find relevant category
        category = self.find_relevant_category(tokens)
        
        if category:
            # Get relevant information
            info = self.knowledge_base[category]['info']
            
            # Find the most relevant piece of information
            response = None
            for key, value in info.items():
                if any(token in key for token in tokens):
                    response = value
                    break
            
            if not response:
                # If no specific match, return general category information
                response = f"Here's what I know about {category}: " + " ".join(info.values())
            
            return response
        else:
            return "I'm sorry, I don't have information about that. Please try asking about payments, students, fee structures, discounts, or reports."

@api_view(['POST'])
def chatbot_query(request):
    if request.method == 'POST':
        query = request.data.get('query', '')
        if not query:
            return Response({'error': 'No query provided'}, status=400)
        
        chatbot = SystemChatbot()
        response = chatbot.get_response(query)
        
        return Response({'response': response})

def chatbot_interface(request):
    return render(request, 'myapp/chatbot.html')

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

# Dashboard View
def dashboard(request):
    return render(request, "dashboard.html")

@api_view(['POST'])
def fpx_payment_request(request):
    # Extract data from request (assuming amount and order_id are passed)
    amount = request.data.get("amount")
    order_id = request.data.get("order_id")
    
    if not amount or not order_id:
        return Response({"error": "Amount and Order ID are required"}, status=400)

    # FPX credentials from settings.py
    fpx_direct_url = settings.FPX_DIRECT_URL
    fpx_api_key = settings.FPX_API_KEY
    fpx_secret = settings.FPX_SECRET

    # Prepare payload (modify as per FPX API docs)
    payload = {
        "order_id": order_id,
        "amount": amount,
        "currency": "MYR",  # Adjust as needed
        "description": "Payment for Order " + str(order_id),
        "return_url": "https://yourwebsite.com/payment/success",
        "cancel_url": "https://yourwebsite.com/payment/cancel",
    }

    # Generate HMAC Signature (if FPX requires it)
    payload_json = json.dumps(payload, separators=(',', ':'))
    signature = hashlib.sha256((payload_json + fpx_secret).encode()).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {fpx_api_key}",
        "X-Signature": signature,
    }

    try:
        # Send request to FPX
        response = requests.post(fpx_direct_url, data=payload_json, headers=headers)
        response_data = response.json()

        # Return response to frontend
        return Response(response_data, status=response.status_code)

    except requests.exceptions.RequestException as e:
        return Response({"error": str(e)}, status=500)

@login_required
def home(request):
    return render(request, 'home.html')

@login_required
def school_fees(request):
    if hasattr(request.user, 'myapp_profile') and request.user.myapp_profile.role == 'student':
        student = request.user.myapp_profile.student
        
        # Get all fee statuses for this student to show payment status
        fee_statuses = FeeStatus.objects.filter(student=student).select_related('fee_structure')
        print(f"DEBUG: views.school_fees - Student {student.first_name} has {len(fee_statuses)} fee statuses")
        print(f"DEBUG: Fee statuses: {[(fs.fee_structure.category.name, fs.status) for fs in fee_statuses[:3]]}")
        
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
        
        context = {
            'student': student,
            'available_fees': available_fees,
            'fee_statuses': fee_statuses,  # Add fee statuses to context
            'recent_payments': student_payments[:5],
            'view_type': 'student',
            'total_payments': total_payments,
            'individual_fees': individual_fees,
        }
        return render(request, 'myapp/school_fees_student.html', context)
    is_tamim = request.user.username == 'tamim123'
    return render(request, 'myapp/school_fees.html', {'is_tamim': is_tamim})

@login_required
def school_fees_dashboard(request):
    from django.db.models import Sum, Count, Q
    from datetime import datetime, timedelta
    from django.db.models.functions import TruncMonth
    import json
    
    # Get filter parameters
    filter_type = request.GET.get('filter_type', 'all')
    filter_value = request.GET.get('filter_value', '')
    status_filter = request.GET.get('status', 'all')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Base queryset for payments
    payments = Payment.objects.select_related('student', 'fee_structure__category')
    
    # Apply filters
    if filter_type == 'student' and filter_value:
        payments = payments.filter(student__first_name__icontains=filter_value)
    elif filter_type == 'class' and filter_value:
        payments = payments.filter(student__class_name__icontains=filter_value)
    elif filter_type == 'category' and filter_value:
        payments = payments.filter(fee_structure__category__name__icontains=filter_value)
    
    if status_filter == 'paid':
        payments = payments.filter(status='completed')
    elif status_filter == 'pending':
        payments = payments.filter(status='pending')
    
    if date_from:
        payments = payments.filter(payment_date__gte=date_from)
    if date_to:
        payments = payments.filter(payment_date__lte=date_to)
    
    # Calculate comprehensive statistics
    total_students = Student.objects.filter(is_active=True).count()
    total_payments_count = payments.count()
    total_paid = payments.filter(status='completed').count()
    pending_payments = payments.filter(status='pending').count()
    overdue_payments = FeeStatus.objects.filter(status='overdue').count()
    
    total_revenue = payments.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
    pending_amount = payments.filter(status='pending').aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Calculate rates
    payment_rate = (total_paid / total_payments_count * 100) if total_payments_count > 0 else 0
    collection_rate = (total_revenue / (total_revenue + pending_amount) * 100) if (total_revenue + pending_amount) > 0 else 0
    
    # Additional metrics
    active_students = Student.objects.filter(is_active=True).count()
    total_fee_structures = FeeStructure.objects.count()
    total_categories = FeeCategory.objects.count()
    paid_fee_statuses = FeeStatus.objects.filter(status='paid').count()
    pending_fee_statuses = FeeStatus.objects.filter(status='pending').count()
    overdue_fee_statuses = FeeStatus.objects.filter(status='overdue').count()
    
    # Get data for charts
    # 1. Payments by Category (Pie Chart)
    category_chart_data = payments.filter(status='completed').values(
        'fee_structure__category__name'
    ).annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    category_chart_labels = [item['fee_structure__category__name'] or 'Individual Fee' for item in category_chart_data]
    category_chart_values = [float(item['total']) for item in category_chart_data]
    
    # 2. Payments by Class (Bar Chart)
    class_chart_data = payments.filter(status='completed').values(
        'student__class_name'
    ).annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    class_chart_labels = [item['student__class_name'] or 'N/A' for item in class_chart_data]
    class_chart_values = [float(item['total']) for item in class_chart_data]
    
    # 3. Monthly Trends (Line Chart)
    six_months_ago = datetime.now() - timedelta(days=180)
    monthly_data = payments.filter(
        status='completed',
        payment_date__gte=six_months_ago
    ).annotate(
        month=TruncMonth('payment_date')
    ).values('month').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('month')
    
    monthly_labels = [data['month'].strftime('%b %Y') for data in monthly_data]
    monthly_amounts = [float(data['total']) for data in monthly_data]
    monthly_counts = [data['count'] for data in monthly_data]
    
    # 4. Status Distribution
    status_distribution = {
        'labels': ['Paid', 'Pending', 'Overdue'],
        'data': [total_paid, pending_payments, overdue_payments]
    }
    
    # Get filter options
    students = Student.objects.all().order_by('first_name')
    classes = Student.objects.values_list('class_name', flat=True).distinct().exclude(class_name__isnull=True).exclude(class_name='')
    categories = FeeCategory.objects.all().order_by('name')
    
    # Recent payments
    recent_payments = payments.order_by('-payment_date')[:10]
    
    # CSV Export
    if request.GET.get('export') == 'csv':
        from django.http import HttpResponse
        import csv
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="payment_analytics.csv"'
        writer = csv.writer(response)
        
        writer.writerow(['Student', 'Class', 'Category', 'Amount', 'Status', 'Date'])
        for payment in payments:
            writer.writerow([
                f"{payment.student.first_name} {payment.student.last_name}",
                payment.student.class_name or 'N/A',
                payment.fee_structure.category.name if payment.fee_structure and payment.fee_structure.category else 'Individual Fee',
                payment.amount,
                payment.status,
                payment.payment_date
            ])
        return response
    
    context = {
        # Filter parameters
        'filter_type': filter_type,
        'filter_value': filter_value,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        
        # Statistics
        'total_students': total_students,
        'total_payments': total_payments_count,
        'total_paid': total_paid,
        'pending_payments': pending_payments,
        'overdue_payments': overdue_payments,
        'total_revenue': total_revenue,
        'active_students': active_students,
        'total_fee_structures': total_fee_structures,
        'total_categories': total_categories,
        'payment_rate': payment_rate,
        'collection_rate': collection_rate,
        'paid_fee_statuses': paid_fee_statuses,
        'pending_fee_statuses': pending_fee_statuses,
        'overdue_fee_statuses': overdue_fee_statuses,
        
        # Chart data
        'category_chart_data': json.dumps({
            'labels': category_chart_labels,
            'data': category_chart_values
        }),
        'class_chart_data': json.dumps({
            'labels': class_chart_labels,
            'data': class_chart_values
        }),
        'monthly_chart_data': json.dumps({
            'labels': monthly_labels,
            'amounts': monthly_amounts,
            'counts': monthly_counts
        }),
        'status_distribution': json.dumps(status_distribution),
        
        # Filter options
        'students': students,
        'classes': classes,
        'categories': categories,
        
        # Recent data
        'recent_payments': recent_payments,
    }
    
    return render(request, 'myapp/school_fees_dashboard.html', context)

@login_required
def student_list(request):
    # Get the show parameter from the request
    show = request.GET.get('show', 'active')
    
    # Filter students based on the show parameter
    if show == 'all':
        students = Student.objects.all()
    else:
        students = Student.objects.filter(is_active=True)
    
    return render(request, 'myapp/student_list.html', {'students': students})

@login_required
def student_detail(request, id):
    student = get_object_or_404(Student, id=id)
    payments = Payment.objects.filter(student=student)
    discounts = FeeDiscount.objects.filter(student=student)
    return render(request, 'myapp/student_detail.html', {
        'student': student,
        'payments': payments,
        'discounts': discounts
    })

@login_required
def add_student(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            student.is_active = request.POST.get('is_active') == 'on'
            student.save()
            messages.success(request, 'Student added successfully!')
            return redirect('myapp:student_list')
    else:
        form = StudentForm()
    return render(request, 'myapp/add_student.html', {'form': form})

@login_required
def fee_structure_list(request):
    # Special logic for tamim123 (student): only show due fees, or empty if all paid
    user = request.user
    is_tamim = user.username == 'tamim123'
    is_student = hasattr(user, 'myapp_profile') and getattr(user.myapp_profile, 'role', None) == 'student'
    fee_structures = FeeStructure.objects.select_related('category')
    if is_tamim and is_student:
        student = user.myapp_profile.student
        from .models import FeeStatus
        due_statuses = FeeStatus.objects.filter(student=student, status__in=['pending', 'overdue'])
        if due_statuses.count() == 0:
            fee_structures = FeeStructure.objects.none()
        else:
            due_fee_ids = due_statuses.values_list('fee_structure_id', flat=True)
            fee_structures = FeeStructure.objects.filter(is_active=True, id__in=due_fee_ids).select_related('category')
    # Failsafe: if student and no due fees, show empty
    elif is_student:
        student = user.myapp_profile.student
        from .models import FeeStatus
        due_statuses = FeeStatus.objects.filter(student=student, status__in=['pending', 'overdue'])
        if due_statuses.count() == 0:
            fee_structures = FeeStructure.objects.none()
    
    # Get individual student fees for the current student (if they are a student) - only unpaid fees
    individual_fees = []
    if is_student:
        try:
            student = user.myapp_profile.student
            individual_fees = IndividualStudentFee.objects.filter(
                student=student, 
                is_active=True,
                is_paid=False  # Only show unpaid fees
            ).select_related('category').order_by('-created_at')
        except:
            individual_fees = []
    
    # Get recent individual student fees for display (only for non-student users)
    recent_individual_fees = []
    if not is_student:
        try:
            recent_individual_fees = IndividualStudentFee.objects.select_related('student', 'category').order_by('-created_at')[:5]
        except:
            recent_individual_fees = []
    
    print(f"DEBUG: username={user.username}, is_student={is_student}, fee_structures_count={fee_structures.count()}")
    return render(request, 'myapp/fee_structure_list.html', {
        'fee_structures': fee_structures,
        'recent_individual_fees': recent_individual_fees,
        'individual_fees': individual_fees,
        'is_tamim': is_tamim
    })

@login_required
def add_fee_structure(request):
    if request.method == 'POST':
        form = FeeStructureForm(request.POST)
        if form.is_valid():
            fee_structure = form.save()
            
            # If auto_generate_payments is enabled, generate payments for all active students
            if fee_structure.auto_generate_payments and fee_structure.frequency == 'monthly':
                from .models import Student
                active_students = Student.objects.filter(is_active=True)
                generated_count = 0
                
                for student in active_students:
                    payments = fee_structure.generate_monthly_payments_for_student(student)
                    generated_count += len(payments)
                
                if generated_count > 0:
                    messages.success(request, f'Fee structure added successfully. Generated {generated_count} monthly payment records for {active_students.count()} students.')
                else:
                    messages.success(request, 'Fee structure added successfully.')
            else:
                messages.success(request, 'Fee structure added successfully.')
            
            return redirect('myapp:fee_structure_list')
        else:
            # Form validation failed
            print(f"DEBUG: Form validation failed. Errors: {form.errors}")
            messages.error(request, 'Please correct the errors below.')
    else:
        form = FeeStructureForm()
    return render(request, 'myapp/add_fee_structure.html', {'form': form})

@login_required
def edit_fee_structure(request, structure_id):
    fee_structure = get_object_or_404(FeeStructure, id=structure_id)
    if request.method == 'POST':
        form = FeeStructureForm(request.POST, instance=fee_structure)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fee structure updated successfully.')
            return redirect('myapp:fee_structure_list')
    else:
        form = FeeStructureForm(instance=fee_structure)
    return render(request, 'myapp/edit_fee_structure.html', {'form': form, 'fee_structure': fee_structure})

@login_required
def delete_fee_structure(request, structure_id):
    fee_structure = get_object_or_404(FeeStructure, id=structure_id)
    if request.method == 'POST':
        fee_structure.delete()
        messages.success(request, 'Fee structure deleted successfully.')
        return redirect('myapp:fee_structure_list')
    return render(request, 'myapp/delete_fee_structure.html', {'fee_structure': fee_structure})

@login_required
def payment_list(request):
    form = PaymentSearchForm(request.GET)
    payments = Payment.objects.select_related('student', 'fee_structure')
    
    if form.is_valid():
        if form.cleaned_data['student']:
            payments = payments.filter(student=form.cleaned_data['student'])
        if form.cleaned_data['month']:
            payments = payments.filter(payment_date__month=form.cleaned_data['month'])
        if form.cleaned_data['year']:
            payments = payments.filter(payment_date__year=form.cleaned_data['year'])
        if form.cleaned_data['status']:
            payments = payments.filter(status=form.cleaned_data['status'])
    
    return render(request, 'myapp/payment_list.html', {
        'payments': payments,
        'form': form
    })

@login_required
def add_payment(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.status = 'completed'  # Set status to completed
            payment.save()
            return redirect('myapp:payment_list')
    else:
        initial_data = {}
        category = request.GET.get('category')
        if category:
            # Get the first fee structure for the selected category
            fee_structure = FeeStructure.objects.filter(
                category__name__icontains=category
            ).first()
            if fee_structure:
                initial_data['fee_structure'] = fee_structure.id
                initial_data['amount'] = fee_structure.amount
        
        form = PaymentForm(initial=initial_data)
    
    return render(request, 'myapp/add_payment.html', {'form': form})

@login_required
def add_discount(request):
    if request.method == 'POST':
        form = FeeDiscountForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Discount added successfully.')
            return redirect('myapp:student_list')
    else:
        form = FeeDiscountForm()
    return render(request, 'myapp/add_discount.html', {'form': form})

@login_required
def bank_accounts(request):
    accounts = SchoolBankAccount.objects.all()
    return render(request, 'myapp/bank_accounts.html', {'accounts': accounts})

@login_required
def add_bank_account(request):
    if request.method == 'POST':
        form = SchoolBankAccountForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bank account added successfully.')
            return redirect('myapp:bank_accounts')
    else:
        form = SchoolBankAccountForm()
    return render(request, 'myapp/add_bank_account.html', {'form': form})

@login_required
def payment_reports(request):
    # Calculate overdue fees (payments with status pending and payment date in the past)
    overdue_payments = Payment.objects.filter(
        payment_date__lt=timezone.now().date(),
        status='pending'
    )
    overdue_amount = overdue_payments.aggregate(total=Sum('amount'))['total'] or 0
    overdue_count = overdue_payments.count()

    # Calculate pending fees (payments with status pending)
    pending_payments = Payment.objects.filter(status='pending')
    pending_amount = pending_payments.aggregate(total=Sum('amount'))['total'] or 0
    pending_count = pending_payments.count()

    # Calculate paid amount (completed payments)
    paid_payments = Payment.objects.filter(status='completed')
    paid_amount = paid_payments.aggregate(total=Sum('amount'))['total'] or 0
    paid_count = paid_payments.count()

    # Calculate remaining amount (total expected - total paid)
    total_expected = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
    remaining_amount = total_expected - paid_amount

    # Monthly payment summary
    monthly_summary = Payment.objects.values('payment_date__year', 'payment_date__month').annotate(
        total_amount=Sum('amount'),
        payment_count=Count('id')
    ).order_by('-payment_date__year', '-payment_date__month')
    
    # Payment status summary
    status_summary = Payment.objects.values('status').annotate(
        count=Count('id'),
        total_amount=Sum('amount')
    )
    
    # Fee category summary
    category_summary = Payment.objects.values('fee_structure__category__name').annotate(
        total_amount=Sum('amount'),
        payment_count=Count('id')
    )
    
    context = {
        'overdue_amount': overdue_amount,
        'overdue_count': overdue_count,
        'pending_amount': pending_amount,
        'pending_count': pending_count,
        'paid_amount': paid_amount,
        'paid_count': paid_count,
        'remaining_amount': remaining_amount,
        'monthly_summary': monthly_summary,
        'status_summary': status_summary,
        'category_summary': category_summary,
    }
    return render(request, 'myapp/payment_reports.html', context)

@login_required
def send_payment_reminder(request, payment_id):
    try:
        print("\n=== Starting Payment Reminder Process ===")
        
        # Get payment
        payment = get_object_or_404(Payment, id=payment_id)
        print(f"Found payment: ID={payment.id}, Amount={payment.amount}")
        
        # Always send to fixed email
        recipient_email = 'moaaj.upm@gmail.com'
        print(f"Using fixed recipient email: {recipient_email}")
        
        # Prepare email content
        subject = f'Payment Reminder - {payment.fee_structure.category.name}'
        context = {
            'payment': payment,
            'now': timezone.now().date(),
        }
        
        # Render email template
        print("Rendering email template...")
        html_message = render_to_string('myapp/email/payment_reminder_email.html', context)
        plain_message = strip_tags(html_message)
        
        print("\n=== Email Content ===")
        print(f"To: {recipient_email}")
        print(f"Subject: {subject}")
        print(f"Message: {plain_message[:200]}...")  # Print first 200 chars
        print("===================\n")
        
        # Send email
        print("Attempting to send email...")
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        print("Email sent successfully!")
        messages.success(request, f'Reminder sent successfully to {recipient_email}')
        
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        messages.error(request, f'Error sending reminder: {str(e)}')
    
    print("=== Payment Reminder Process Complete ===\n")
    return redirect('payment_reminders')

@login_required
def payment_reminders(request):
    # Get all pending payments
    pending_payments = Payment.objects.filter(
        status='pending'
    ).select_related('student', 'fee_structure').order_by('payment_date')
    
    # Separate overdue and upcoming payments
    today = timezone.now().date()
    overdue_payments = pending_payments.filter(payment_date__lt=today)
    upcoming_payments = pending_payments.filter(payment_date__gte=today)
    
    context = {
        'overdue_payments': overdue_payments,
        'upcoming_payments': upcoming_payments,
        'total_overdue': overdue_payments.aggregate(total=Sum('amount'))['total'] or 0,
        'total_upcoming': upcoming_payments.aggregate(total=Sum('amount'))['total'] or 0,
    }
    return render(request, 'myapp/payment_reminders.html', context)

@login_required
def donation_categories(request):
    categories = DonationCategory.objects.all()
    return render(request, 'myapp/donation_categories.html', {'categories': categories})

@login_required
def add_donation_category(request):
    if request.method == 'POST':
        form = DonationCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category added successfully.')
            return redirect('donation_categories')
    else:
        form = DonationCategoryForm()
    return render(request, 'myapp/add_donation_category.html', {'form': form})

@login_required
def donation_events(request):
    events = DonationEvent.objects.filter(is_active=True)
    return render(request, 'myapp/donation_events.html', {'events': events})

@login_required
def add_donation_event(request):
    if request.method == 'POST':
        form = DonationEventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = None
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(f"{settings.SITE_URL}/donate/{event.id}/")
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            
            # Save QR code
            filename = f'qr_{event.id}.png'
            event.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)
            
            event.save()
            messages.success(request, 'Event added successfully.')
            return redirect('donation_events')
    else:
        form = DonationEventForm()
    return render(request, 'myapp/add_donation_event.html', {'form': form})

@login_required
def donation_event_detail(request, event_id):
    event = get_object_or_404(DonationEvent, id=event_id)
    return render(request, 'myapp/donation_event_detail.html', {'event': event})

@login_required
def make_donation(request, event_id):
    event = get_object_or_404(DonationEvent, id=event_id)
    
    if request.method == 'POST':
        form = DonationForm(request.POST)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.event = event
            donation.status = 'completed'  # Assuming payment is processed successfully
            donation.save()
            
            return redirect('donation_success', donation_id=donation.id)
    else:
        form = DonationForm()
    
    return render(request, 'myapp/make_donation.html', {
        'form': form,
        'event': event
    })

@login_required
def donation_success(request, donation_id):
    donation = get_object_or_404(Donation, id=donation_id)
    return render(request, 'myapp/donation_success.html', {'donation': donation})

@login_required
def donate(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')
        name = request.POST.get('name', 'Anonymous Donor')
        
        # Create PDF using reportlab instead of WeasyPrint
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="donation_certificate_{name}.pdf"'
        
        # Create the PDF object
        p = canvas.Canvas(response, pagesize=letter)
        width, height = letter
        
        # Add title
        p.setFont("Helvetica-Bold", 24)
        p.drawCentredString(width/2, height - 100, "Donation Certificate")
        
        # Add certificate content
        p.setFont("Helvetica", 14)
        p.drawCentredString(width/2, height - 150, f"This certificate is presented to")
        
        p.setFont("Helvetica-Bold", 18)
        p.drawCentredString(width/2, height - 180, name)
        
        p.setFont("Helvetica", 14)
        p.drawCentredString(width/2, height - 210, "in recognition of their generous donation of")
        
        p.setFont("Helvetica-Bold", 16)
        p.drawCentredString(width/2, height - 240, f"RM {amount}")
        
        p.setFont("Helvetica", 12)
        p.drawCentredString(width/2, height - 280, f"Date: {datetime.now().strftime('%B %d, %Y')}")
        
        p.setFont("Helvetica", 10)
        p.drawCentredString(width/2, height - 320, "Thank you for your support!")
        p.drawCentredString(width/2, height - 340, "Your contribution makes a difference.")
        
        p.showPage()
        p.save()
        return response
    
    return render(request, 'myapp/donate.html')

@login_required
def payment_receipt(request, payment_id):
    try:
        payment = get_object_or_404(Payment, id=payment_id)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="payment_receipt_{payment.id}.pdf"'
        p = canvas.Canvas(response, pagesize=letter)
        width, height = letter
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, "Payment Receipt")
        p.setFont("Helvetica", 12)
        # Use receipt_number if available, otherwise fallback to payment.id
        receipt_no = payment.receipt_number if payment.receipt_number else payment.id
        p.drawString(50, height - 80, f"Receipt Number: #{receipt_no}")
        p.drawString(50, height - 100, f"Date: {payment.payment_date}")
        p.drawString(50, height - 120, f"Status: {payment.status.title()}")
        p.drawString(50, height - 160, f"Student: {payment.student}")
        if payment.fee_structure:
            p.drawString(50, height - 180, f"Fee Structure: {payment.fee_structure}")
        p.drawString(50, height - 220, f"Payment Method: {payment.get_payment_method_display()}")
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, height - 260, f"Amount Paid: ${payment.amount}")
        p.setFont("Helvetica", 10)
        p.drawString(50, 50, "Thank you for your payment!")
        p.drawString(50, 30, "This receipt serves as proof of your payment.")
        p.showPage()
        p.save()
        return response
    except Exception as e:
        messages.error(request, f"Error generating receipt: {str(e)}")
        return redirect('myapp:payment_list')

@login_required
def edit_payment(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    students = Student.objects.filter(is_active=True)
    fee_structures = FeeStructure.objects.all()
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payment updated successfully.')
            return redirect('myapp:payment_list')
    else:
        form = PaymentForm(instance=payment)
    
    context = {
        'form': form,
        'payment': payment,
        'students': students,
        'fee_structures': fee_structures
    }
    return render(request, 'myapp/edit_payment.html', context)

@login_required
def delete_payment(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if request.method == 'POST':
        payment.delete()
        return redirect('myapp:payment_list')
    return render(request, 'myapp/delete_payment_confirm.html', {'payment': payment})

@login_required
def fee_categories(request):
    categories = FeeCategory.objects.all()
    return render(request, 'myapp/fee_categories.html', {'categories': categories})

@login_required
def add_fee_category(request):
    if request.method == 'POST':
        form = FeeCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fee category added successfully.')
            return redirect('myapp:fee_categories')
    else:
        form = FeeCategoryForm()
    return render(request, 'myapp/add_fee_category.html', {'form': form})

@login_required
def edit_fee_category(request, category_id):
    category = get_object_or_404(FeeCategory, id=category_id)
    if request.method == 'POST':
        form = FeeCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fee category updated successfully.')
            return redirect('myapp:fee_categories')
    else:
        form = FeeCategoryForm(instance=category)
    return render(request, 'myapp/edit_fee_category.html', {'form': form, 'category': category})

@login_required
def delete_fee_category(request, category_id):
    category = get_object_or_404(FeeCategory, id=category_id)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Fee category deleted successfully.')
        return redirect('myapp:fee_categories')
    return render(request, 'myapp/delete_fee_category.html', {'category': category})

@login_required
def payment_receipts(request):
    # Get all completed payments with receipts
    payments = Payment.objects.filter(
        status='completed'
    ).select_related('student', 'fee_structure').order_by('-payment_date')
    
    context = {
        'payments': payments,
    }
    return render(request, 'myapp/payment_receipts.html', context)

@login_required
def email_preferences(request):
    if request.method == 'POST':
        # Get the current user's preferences or create new ones
        preferences, created = EmailPreferences.objects.get_or_create(user=request.user)
        
        # Update preferences based on form data
        preferences.receive_payment_receipts = request.POST.get('receive_payment_receipts') == 'on'
        preferences.receive_payment_reminders = request.POST.get('receive_payment_reminders') == 'on'
        preferences.receive_monthly_statements = request.POST.get('receive_monthly_statements') == 'on'
        preferences.email_address = 'moaaj.upm@gmail.com'  # Set default email
        preferences.save()
        
        messages.success(request, 'Email preferences updated successfully.')
        return redirect('email_preferences')
    
    # Get existing preferences or create default ones
    preferences, created = EmailPreferences.objects.get_or_create(
        user=request.user,
        defaults={
            'email_address': 'moaaj.upm@gmail.com',  # Set default email
            'receive_payment_receipts': True,
            'receive_payment_reminders': True,
            'receive_monthly_statements': True
        }
    )
    
    return render(request, 'myapp/email_preferences.html', {'preferences': preferences})

@login_required
def print_receipts(request):
    # Get all completed payments with receipts
    payments = Payment.objects.filter(
        status='completed'
    ).select_related('student', 'fee_structure').order_by('-payment_date')
    
    context = {
        'payments': payments,
    }
    return render(request, 'myapp/print_receipts.html', context)

@login_required
def email_receipt(request, payment_id):
    try:
        print("\n=== Starting Email Process ===")
        
        # Get payment
        payment = get_object_or_404(Payment, id=payment_id)
        print(f"Found payment: ID={payment.id}, Amount={payment.amount}")
        
        # Basic email content
        subject = f'Payment Receipt - {payment.id}'
        message = f"""
        Payment Receipt
        
        Student: {payment.student.first_name} {payment.student.last_name}
        Amount: RM {payment.amount}
        Date: {payment.payment_date}
        Payment Method: {payment.payment_method}
        
        Thank you for your payment!
        """
        
        print("\n=== Email Content ===")
        print(f"To: moaaj.upm@gmail.com")
        print(f"Subject: {subject}")
        print(f"Message: {message}")
        print("===================\n")
        
        # Try to send email
        print("Attempting to send email...")
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['moaaj.upm@gmail.com'],
            fail_silently=False,
        )
        
        print("Email sent successfully!")
        messages.success(request, 'Email has been sent to moaaj.upm@gmail.com')
        
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        messages.error(request, f'Error sending email: {str(e)}')
    
    print("=== Email Process Complete ===\n")
    return redirect('payment_receipts')

@login_required
def pending_fees(request):
    # Get all pending and overdue fees
    fee_statuses = FeeStatus.objects.filter(
        status__in=['pending', 'overdue']
    ).select_related('student', 'fee_structure').order_by('due_date')
    
    # Update status of all fees
    for fee_status in fee_statuses:
        fee_status.update_status()
    
    # Get summary statistics
    total_pending = fee_statuses.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0
    total_overdue = fee_statuses.filter(status='overdue').aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'fee_statuses': fee_statuses,
        'total_pending': total_pending,
        'total_overdue': total_overdue,
    }
    return render(request, 'myapp/pending_fees.html', context)

@login_required
def add_fee_status(request):
    if request.method == 'POST':
        student_id = request.POST.get('student')
        fee_structure_id = request.POST.get('fee_structure')
        amount = request.POST.get('amount')
        due_date = request.POST.get('due_date')
        
        try:
            student = Student.objects.get(id=student_id)
            fee_structure = FeeStructure.objects.get(id=fee_structure_id)
            
            fee_status = FeeStatus.objects.create(
                student=student,
                fee_structure=fee_structure,
                amount=amount,
                due_date=due_date,
                status='pending'
            )
            
            messages.success(request, 'Fee status added successfully.')
            return redirect('pending_fees')
        except (Student.DoesNotExist, FeeStructure.DoesNotExist):
            messages.error(request, 'Invalid student or fee structure.')
    
    students = Student.objects.all()
    fee_structures = FeeStructure.objects.all()
    return render(request, 'myapp/add_fee_status.html', {
        'students': students,
        'fee_structures': fee_structures
    })

@login_required
def update_fee_status(request, fee_status_id):
    fee_status = get_object_or_404(FeeStatus, id=fee_status_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(FeeStatus.STATUS_CHOICES):
            fee_status.status = new_status
            fee_status.save()
            messages.success(request, 'Fee status updated successfully.')
            return redirect('pending_fees')
    
    return render(request, 'myapp/update_fee_status.html', {'fee_status': fee_status})

@login_required
def generate_reminder_letter(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    
    # Create the HttpResponse object with PDF headers
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reminder_{payment.id}.pdf"'
    
    # Create the PDF object
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    
    # Add content to PDF
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, "Payment Reminder")
    
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 80, f"Dear {payment.student.name},")
    p.drawString(50, height - 100, f"This is a reminder that payment of ${payment.amount:.2f}")
    p.drawString(50, height - 120, f"for {payment.fee_structure.category.name} is due.")
    p.drawString(50, height - 140, f"Due Date: {payment.payment_date.strftime('%Y-%m-%d')}")
    
    # Save the PDF
    p.showPage()
    p.save()
    
    return response

@login_required
def fee_waivers(request):
    waivers = FeeWaiver.objects.select_related('student', 'category').all().order_by('-created_at')
    return render(request, 'myapp/fee_waivers.html', {'waivers': waivers})

@login_required
def add_fee_waiver(request):
    if request.method == 'POST':
        form = FeeWaiverForm(request.POST)
        if form.is_valid():
            try:
                fee_waiver = form.save(commit=False)
                # Get or create the fee category
                category_name = form.cleaned_data['category']
                category, created = FeeCategory.objects.get_or_create(name=category_name)
                fee_waiver.category = category
                
                # Get or create the student
                student_id = form.cleaned_data['student_id']
                student, created = Student.objects.get_or_create(
                    student_id=student_id,
                    defaults={
                        'first_name': form.cleaned_data['student_name'].split()[0],
                        'last_name': ' '.join(form.cleaned_data['student_name'].split()[1:]) if len(form.cleaned_data['student_name'].split()) > 1 else '',
                        'year_batch': datetime.now().year,
                        'nric': f"TEMP-{student_id}"  # Temporary NRIC since it's required
                    }
                )
                fee_waiver.student = student
                
                # Store student information in the reason field
                student_info = f"Student Name: {form.cleaned_data['student_name']}\n"
                student_info += f"Student Class: {form.cleaned_data['student_class']}\n"
                student_info += f"Student ID: {form.cleaned_data['student_id']}\n\n"
                student_info += f"Reason: {form.cleaned_data['reason']}"
                fee_waiver.reason = student_info
                fee_waiver.status = 'pending'
                fee_waiver.save()
                messages.success(request, 'Fee waiver request submitted successfully.')
                return redirect('fee_waivers')
            except Exception as e:
                messages.error(request, f'Error saving fee waiver: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = FeeWaiverForm()
    
    return render(request, 'myapp/add_fee_waiver.html', {'form': form})

@login_required
def approve_fee_waiver(request, waiver_id):
    if request.method == 'POST':
        waiver = get_object_or_404(FeeWaiver, id=waiver_id)
        if waiver.status == 'pending':
            waiver.status = 'approved'
            waiver.approved_by = None
            waiver.approved_date = timezone.now()
            waiver.save()
            messages.success(request, 'Fee waiver has been approved successfully.')
        else:
            messages.error(request, 'This waiver cannot be approved.')
    return redirect('myapp:fee_waivers')

@login_required
def reject_fee_waiver(request, waiver_id):
    if request.method == 'POST':
        waiver = get_object_or_404(FeeWaiver, id=waiver_id)
        if waiver.status == 'pending':
            waiver.status = 'rejected'
            waiver.save()
            messages.success(request, 'Fee waiver has been rejected.')
        else:
            messages.error(request, 'This waiver cannot be rejected.')
    return redirect('fee_waivers')

@login_required
def view_fee_waiver_letter(request, waiver_id):
    waiver = get_object_or_404(FeeWaiver, id=waiver_id)
    
    # Create the HTTP response with PDF content type
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="fee_waiver_{waiver_id}.pdf"'
    
    # Create the PDF object
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    
    # Add content to PDF
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, "Fee Waiver Letter")
    
    p.setFont("Helvetica", 12)
    # Handle case where student is None
    student_name = "N/A"
    if waiver.student:
        student_name = f"{waiver.student.first_name} {waiver.student.last_name}"
    p.drawString(50, height - 80, f"Student: {student_name}")
    
    # Handle case where category is None
    category_name = "N/A"
    if waiver.category:
        category_name = waiver.category.name
    p.drawString(50, height - 100, f"Category: {category_name}")
    
    p.drawString(50, height - 120, f"Amount: ${waiver.amount:.2f}")
    p.drawString(50, height - 140, f"Status: {waiver.status}")
    p.drawString(50, height - 160, f"Reason: {waiver.reason}")
    
    # Save the PDF
    p.showPage()
    p.save()
    
    return response

@login_required
def fee_reports(request):
    # Get date range from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Base querysets
    collected_payments = Payment.objects.filter(status='completed')
    pending_payments = Payment.objects.filter(status='pending')
    waived_fees = FeeWaiver.objects.filter(status='approved')
    
    # Apply date filters if provided
    if start_date:
        collected_payments = collected_payments.filter(payment_date__gte=start_date)
        pending_payments = pending_payments.filter(payment_date__gte=start_date)
        waived_fees = waived_fees.filter(start_date__gte=start_date)
    
    if end_date:
        collected_payments = collected_payments.filter(payment_date__lte=end_date)
        pending_payments = pending_payments.filter(payment_date__lte=end_date)
        waived_fees = waived_fees.filter(end_date__lte=end_date)
    
    # Add related fields
    collected_payments = collected_payments.select_related('student', 'fee_structure__category')
    pending_payments = pending_payments.select_related('student', 'fee_structure__category')
    
    # Calculate totals
    total_collected = collected_payments.aggregate(total=Sum('amount'))['total'] or 0
    total_pending = pending_payments.aggregate(total=Sum('amount'))['total'] or 0
    
    # Calculate total waived amount
    total_waived = 0
    for waiver in waived_fees:
        if waiver.percentage:
            avg_fee = Payment.objects.filter(
                fee_structure__category=waiver.category
            ).aggregate(avg=Avg('amount'))['avg'] or 0
            total_waived += (avg_fee * waiver.percentage / 100)
        else:
            total_waived += waiver.amount or 0
    
    # Get counts
    collected_count = collected_payments.count()
    pending_count = pending_payments.count()
    waived_count = waived_fees.count()
    
    # Generate category summary
    categories = FeeCategory.objects.all()
    category_summary = []
    
    for category in categories:
        category_collected = collected_payments.filter(
            fee_structure__category=category
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        category_pending = pending_payments.filter(
            fee_structure__category=category
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        category_waived = 0
        category_waivers = waived_fees.filter(category=category)
        for waiver in category_waivers:
            if waiver.percentage:
                avg_fee = Payment.objects.filter(
                    fee_structure__category=category
                ).aggregate(avg=Avg('amount'))['avg'] or 0
                category_waived += (avg_fee * waiver.percentage / 100)
            else:
                category_waived += waiver.amount or 0
        
        category_total = category_collected + category_pending + category_waived
        
        category_summary.append({
            'name': category.name,
            'collected': category_collected,
            'pending': category_pending,
            'waived': category_waived,
            'total': category_total
        })
    
    context = {
        'collected_payments': collected_payments,
        'pending_payments': pending_payments,
        'waived_fees': waived_fees,
        'total_collected': total_collected,
        'total_pending': total_pending,
        'total_waived': total_waived,
        'collected_count': collected_count,
        'pending_count': pending_count,
        'waived_count': waived_count,
        'category_summary': category_summary,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'myapp/fee_reports.html', context)

@login_required
def export_fee_report(request):
    # Get date range from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Get the same data as fee_reports view
    collected_payments = Payment.objects.filter(status='completed')
    pending_payments = Payment.objects.filter(status='pending')
    waived_fees = FeeWaiver.objects.filter(status='approved')
    
    # Apply date filters if provided
    if start_date:
        collected_payments = collected_payments.filter(payment_date__gte=start_date)
        pending_payments = pending_payments.filter(payment_date__gte=start_date)
        waived_fees = waived_fees.filter(start_date__gte=start_date)
    
    if end_date:
        collected_payments = collected_payments.filter(payment_date__lte=end_date)
        pending_payments = pending_payments.filter(payment_date__lte=end_date)
        waived_fees = waived_fees.filter(end_date__lte=end_date)
    
    # Add related fields
    collected_payments = collected_payments.select_related('student', 'fee_structure__category')
    pending_payments = pending_payments.select_related('student', 'fee_structure__category')
    
    # Create Excel workbook
    wb = Workbook()
    
    # Summary Sheet
    ws_summary = wb.active
    ws_summary.title = "Summary"
    ws_summary.append(['Fee Category', 'Collected', 'Pending', 'Waived', 'Total'])
    
    # Get category summary
    categories = FeeCategory.objects.all()
    for category in categories:
        category_collected = collected_payments.filter(
            fee_structure__category=category
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        category_pending = pending_payments.filter(
            fee_structure__category=category
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        category_waived = 0
        category_waivers = waived_fees.filter(category=category)
        for waiver in category_waivers:
            if waiver.percentage:
                avg_fee = Payment.objects.filter(
                    fee_structure__category=category
                ).aggregate(avg=Avg('amount'))['avg'] or 0
                category_waived += (avg_fee * waiver.percentage / 100)
            else:
                category_waived += waiver.amount or 0
        
        category_total = category_collected + category_pending + category_waived
        
        # Add row to summary sheet
        ws_summary.append([
            category.name,
            float(category_collected),
            float(category_pending),
            float(category_waived),
            float(category_total)
        ])
    
    # Collected Payments Sheet
    ws_collected = wb.create_sheet("Collected Payments")
    ws_collected.append(['Date', 'Student', 'Category', 'Amount', 'Payment Method'])
    
    for payment in collected_payments:
        ws_collected.append([
            payment.payment_date,
            f"{payment.student.first_name} {payment.student.last_name}",
            payment.fee_structure.category.name if payment.fee_structure else 'N/A',
            float(payment.amount),
            payment.payment_method
        ])

    # Pending Payments Sheet
    ws_pending = wb.create_sheet("Pending Payments")
    ws_pending.append(['Date', 'Student', 'Category', 'Amount', 'Payment Method'])
    
    for payment in pending_payments:
        ws_pending.append([
            payment.payment_date,
            f"{payment.student.first_name} {payment.student.last_name}",
            payment.fee_structure.category.name if payment.fee_structure else 'N/A',
            float(payment.amount),
            payment.payment_method
        ])

    # Waived Fees Sheet
    ws_waived = wb.create_sheet("Waived Fees")
    ws_waived.append(['Student', 'Category', 'Amount', 'Percentage', 'Start Date', 'End Date'])
    
    for waiver in waived_fees:
        ws_waived.append([
            f"{waiver.student.first_name} {waiver.student.last_name}" if waiver.student else 'N/A',
            waiver.category.name if waiver.category else 'N/A',
            float(waiver.amount) if waiver.amount else 0,
            float(waiver.percentage) if waiver.percentage else 0,
            waiver.start_date,
            waiver.end_date
        ])

    # Create response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=fee_report.xlsx'
    
    # Save workbook to response
    wb.save(response)
    
    return response

@login_required
def edit_student(request, id):
    student = get_object_or_404(Student, id=id)
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            student = form.save(commit=False)
            student.is_active = request.POST.get('is_active') == 'on'
            student.save()
            messages.success(request, 'Student updated successfully!')
            return redirect('myapp:student_list')
    else:
        form = StudentForm(instance=student)
    return render(request, 'myapp/edit_student.html', {'form': form, 'student': student})

@login_required
def delete_student(request, id):
    student = get_object_or_404(Student, id=id)
    if request.method == 'POST':
        student.delete()
        messages.success(request, 'Student deleted successfully!')
        return redirect('myapp:student_list')
    return render(request, 'myapp/delete_student_confirm.html', {'student': student})

@login_required
def fee_analytics_dashboard(request):
    # Get date range from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Base querysets
    collected_payments = Payment.objects.filter(status='completed')
    pending_payments = Payment.objects.filter(status='pending')
    overdue_payments = Payment.objects.filter(
        payment_date__lt=timezone.now().date(),
        status='pending'
    )
    
    # Apply date filters if provided
    if start_date:
        collected_payments = collected_payments.filter(payment_date__gte=start_date)
        pending_payments = pending_payments.filter(payment_date__gte=start_date)
        overdue_payments = overdue_payments.filter(payment_date__gte=start_date)
    
    if end_date:
        collected_payments = collected_payments.filter(payment_date__lte=end_date)
        pending_payments = pending_payments.filter(payment_date__lte=end_date)
        overdue_payments = overdue_payments.filter(payment_date__lte=end_date)
    
    # Calculate totals
    total_collected = collected_payments.aggregate(total=Sum('amount'))['total'] or 0
    total_pending = pending_payments.aggregate(total=Sum('amount'))['total'] or 0
    overdue_amount = overdue_payments.aggregate(total=Sum('amount'))['total'] or 0
    
    # Get counts
    paid_count = collected_payments.count()
    
    # Get monthly data for trends
    monthly_data = Payment.objects.annotate(
        month=TruncMonth('payment_date')
    ).values('month').annotate(
        collected=Sum('amount', filter=Q(status='completed')),
        pending=Sum('amount', filter=Q(status='pending'))
    ).order_by('month')[:12]
    
    monthly_labels = [data['month'].strftime('%b %Y') for data in monthly_data]
    monthly_collected = [float(data['collected'] or 0) for data in monthly_data]
    monthly_pending = [float(data['pending'] or 0) for data in monthly_data]
    
    # Get category data
    categories = FeeCategory.objects.all()
    category_labels = [category.name for category in categories]
    category_collected = []
    category_pending = []
    
    for category in categories:
        category_collected.append(float(collected_payments.filter(
            fee_structure__category=category
        ).aggregate(total=Sum('amount'))['total'] or 0))
        
        category_pending.append(float(pending_payments.filter(
            fee_structure__category=category
        ).aggregate(total=Sum('amount'))['total'] or 0))
    
    # Get recent payments
    recent_payments = Payment.objects.select_related(
        'student', 'fee_structure__category'
    ).order_by('-payment_date')[:5]
    
    context = {
        'total_collected': total_collected,
        'total_pending': total_pending,
        'overdue_amount': overdue_amount,
        'paid_count': paid_count,
        'monthly_labels': monthly_labels,
        'monthly_collected': monthly_collected,
        'monthly_pending': monthly_pending,
        'category_labels': category_labels,
        'category_collected': category_collected,
        'category_pending': category_pending,
        'recent_payments': recent_payments,
    }
    
    return render(request, 'myapp/fee_analytics_dashboard.html', context)

@login_required
def fee_settings(request):
    return render(request, 'myapp/fee_settings.html')

@login_required
def edit_term(request, term_id):
    term = get_object_or_404(AcademicTerm, id=term_id)
    
    if request.method == 'POST':
        term.name = request.POST.get('term_name')
        term.start_date = request.POST.get('start_date')
        term.end_date = request.POST.get('end_date')
        term.save()
        messages.success(request, 'Academic term updated successfully.')
        return redirect('fee_settings')
    
    return JsonResponse({
        'id': term.id,
        'name': term.name,
        'start_date': term.start_date.strftime('%Y-%m-%d'),
        'end_date': term.end_date.strftime('%Y-%m-%d')
    })

@login_required
def delete_term(request, term_id):
    term = get_object_or_404(AcademicTerm, id=term_id)
    term.delete()
    messages.success(request, 'Academic term deleted successfully.')
    return redirect('fee_settings')

@login_required
def ai_fee_analytics(request):
    """View for AI-powered fee analytics and predictions"""
    prediction_service = PaymentPredictionService()
    
    # Get next month's payment predictions
    next_month_predictions = prediction_service.predict_next_month_payments()
    
    # Get fee structure recommendations
    fee_recommendations = prediction_service.get_fee_structure_recommendations()
    
    # Get risk assessment for all students with pending payments
    pending_payments = Payment.objects.filter(status='pending').select_related('student')
    student_risks = {}
    
    for payment in pending_payments:
        if payment.student.id not in student_risks:
            risk = prediction_service.get_payment_risk_assessment(payment.student.id)
            student_risks[payment.student.id] = {
                'student': payment.student,
                'risk_assessment': risk
            }
    
    context = {
        'next_month_predictions': next_month_predictions,
        'fee_recommendations': fee_recommendations,
        'student_risks': student_risks,
    }
    
    return render(request, 'myapp/ai_fee_analytics.html', context)

@login_required
def donation_prediction(request):
    """View for donation prediction analytics"""
    prediction_service = PaymentPredictionService()
    predictions = prediction_service.predict_next_month_payments()
    
    context = {
        'predictions': predictions,
        'title': 'Donation Prediction'
    }
    return render(request, 'myapp/donation_prediction.html', context)

@login_required
def donor_insights(request):
    """View for donor behavior insights"""
    context = {
        'title': 'Donor Insights'
    }
    return render(request, 'myapp/donor_insights.html', context)

@login_required
def ai_settings(request):
    """View for AI feature settings"""
    context = {
        'title': 'AI Settings'
    }
    return render(request, 'myapp/ai_settings.html', context)

@login_required
def bulk_upload_students(request):
    print("DEBUG: bulk_upload_students view called")
    if request.method == 'POST':
        print("DEBUG: POST request received")
        print("DEBUG: FILES:", request.FILES)
        if 'file' not in request.FILES:
            messages.error(request, 'Please select a file to upload.')
            return redirect('bulk_upload_students')
        
        file = request.FILES['file']
        if not file.name.endswith(('.xlsx', '.xls', '.csv')):
            messages.error(request, 'Please upload an Excel (.xlsx, .xls) or CSV file.')
            return redirect('bulk_upload_students')
        
        try:
            # Read the file
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
            
            # Validate required columns
            required_columns = ['student_id', 'nric', 'first_name', 'last_name', 'year_batch']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                messages.error(request, f'Missing required columns: {", ".join(missing_columns)}')
                return redirect('bulk_upload_students')
            
            # Process each row
            success_count = 0
            error_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Check if student already exists
                    if Student.objects.filter(student_id=row['student_id']).exists():
                        errors.append(f"Row {index + 2}: Student ID {row['student_id']} already exists")
                        error_count += 1
                        continue
                    
                    if Student.objects.filter(nric=row['nric']).exists():
                        errors.append(f"Row {index + 2}: NRIC {row['nric']} already exists")
                        error_count += 1
                        continue
                    
                    # Create new student
                    student = Student(
                        student_id=row['student_id'],
                        nric=row['nric'],
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        year_batch=row['year_batch'],
                        is_active=True
                    )
                    student.save()
                    success_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {index + 2}: {str(e)}")
                    error_count += 1
            
            # Show results
            if success_count > 0:
                messages.success(request, f'Successfully added {success_count} students.')
            if error_count > 0:
                messages.warning(request, f'Failed to add {error_count} students. See details below.')
                for error in errors:
                    messages.error(request, error)
            
            return redirect('student_list')
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error processing file: {str(e)}')
            return redirect('bulk_upload_students')
    
    return render(request, 'myapp/bulk_upload_students.html')

@login_required
def download_student_template(request):
    # Create a new workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Students Template"
    
    # Add headers
    headers = ['student_id', 'nric', 'first_name', 'last_name', 'year_batch']
    ws.append(headers)
    
    # Add example row
    example = ['STU001', '123456-78-9012', 'John', 'Doe', '2024']
    ws.append(example)
    
    # Create response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=student_template.xlsx'
    
    # Save workbook to response
    wb.save(response)
    return response

@login_required
def donation_receipt(request, donation_id):
    try:
        # Get donation with related data
        donation = get_object_or_404(
            Donation.objects.select_related('event'),
            id=donation_id
        )
        
        # Create the HttpResponse object with PDF headers
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="donation_receipt_{donation.id}.pdf"'
        
        # Create the PDF object
        p = canvas.Canvas(response, pagesize=letter)
        width, height = letter
        
        # Add school logo or header
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, "Donation Receipt")
        
        # Add receipt details
        p.setFont("Helvetica", 12)
        p.drawString(50, height - 80, f"Receipt Number: #{donation.id}")
        p.drawString(50, height - 100, f"Date: {donation.created_at.strftime('%Y-%m-%d')}")
        p.drawString(50, height - 120, f"Status: {donation.status.title()}")
        
        # Add donor information
        p.drawString(50, height - 160, f"Donor Name: {donation.donor_name}")
        p.drawString(50, height - 180, f"Donor Email: {donation.donor_email}")
        
        # Add donation details
        p.drawString(50, height - 220, f"Event: {donation.event.title}")
        
        # Get payment method display value
        payment_method_display = dict(Donation.PAYMENT_METHODS).get(donation.payment_method, donation.payment_method)
        p.drawString(50, height - 240, f"Payment Method: {payment_method_display}")
        
        if donation.transaction_id:
            p.drawString(50, height - 260, f"Transaction ID: {donation.transaction_id}")
        
        # Add amount
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, height - 300, f"Amount Donated: ${donation.amount}")
        
        # Add message if exists
        if donation.message:
            p.setFont("Helvetica", 12)
            p.drawString(50, height - 340, "Message:")
            p.drawString(50, height - 360, donation.message)
        
        # Add footer
        p.setFont("Helvetica", 10)
        p.drawString(50, 50, "Thank you for your generous donation!")
        p.drawString(50, 30, "This receipt serves as proof of your donation.")
        
        # Save the PDF
        p.showPage()
        p.save()
        
        return response
        
    except Exception as e:
        messages.error(request, f"Error generating receipt: {str(e)}")
        return redirect('donation_success', donation_id=donation_id)

@login_required
def individual_student_fees(request):
    """List all individual student fees"""
    fees = IndividualStudentFee.objects.select_related('student', 'category').order_by('-created_at')
    
    # Filter by student if provided
    student_id = request.GET.get('student')
    if student_id:
        fees = fees.filter(student_id=student_id)
    
    # Filter by status if provided
    status = request.GET.get('status')
    if status == 'pending':
        fees = fees.filter(is_paid=False)
    elif status == 'paid':
        fees = fees.filter(is_paid=True)
    elif status == 'overdue':
        from django.utils import timezone
        fees = fees.filter(is_paid=False, due_date__lt=timezone.now().date())
    
    context = {
        'fees': fees,
        'students': Student.objects.filter(is_active=True),
    }
    return render(request, 'myapp/individual_student_fees.html', context)

@login_required
def add_individual_student_fee(request):
    """Add a new individual student fee"""
    if request.method == 'POST':
        form = IndividualStudentFeeForm(request.POST)
        if form.is_valid():
            fee = form.save(commit=False)
            fee.created_by = request.user
            fee.save()
            
            # Add success message with student name for clarity
            student_name = f"{fee.student.first_name} {fee.student.last_name}"
            messages.success(request, f'Individual student fee "{fee.name}" (RM {fee.amount}) added successfully for {student_name}.')
            
            return redirect('myapp:individual_student_fees')
    else:
        form = IndividualStudentFeeForm()
        
        # Pre-select category based on URL parameter
        category_param = request.GET.get('category')
        if category_param:
            if category_param == 'overtime':
                try:
                    overtime_category = FeeCategory.objects.get(name='Overtime', category_type='individual')
                    form.fields['category'].initial = overtime_category
                except FeeCategory.DoesNotExist:
                    pass
            elif category_param == 'demerit':
                try:
                    demerit_category = FeeCategory.objects.get(name='Demerit Penalties', category_type='individual')
                    form.fields['category'].initial = demerit_category
                except FeeCategory.DoesNotExist:
                    pass
    
    context = {
        'form': form,
        'title': 'Add Individual Student Fee'
    }
    return render(request, 'myapp/add_individual_student_fee.html', context)

@login_required
def edit_individual_student_fee(request, fee_id):
    """Edit an individual student fee"""
    fee = get_object_or_404(IndividualStudentFee, id=fee_id)
    
    if request.method == 'POST':
        form = IndividualStudentFeeForm(request.POST, instance=fee)
        if form.is_valid():
            form.save()
            messages.success(request, 'Individual student fee updated successfully.')
            return redirect('myapp:individual_student_fees')
    else:
        form = IndividualStudentFeeForm(instance=fee)
    
    context = {
        'form': form,
        'fee': fee,
        'title': 'Edit Individual Student Fee'
    }
    return render(request, 'myapp/add_individual_student_fee.html', context)

@login_required
def delete_individual_student_fee(request, fee_id):
    """Delete an individual student fee"""
    fee = get_object_or_404(IndividualStudentFee, id=fee_id)
    
    if request.method == 'POST':
        fee.delete()
        messages.success(request, 'Individual student fee deleted successfully.')
        return redirect('myapp:individual_student_fees')
    
    context = {
        'fee': fee
    }
    return render(request, 'myapp/delete_individual_student_fee.html', context)

@login_required
def mark_fee_as_paid(request, fee_id):
    """Mark an individual student fee as paid"""
    fee = get_object_or_404(IndividualStudentFee, id=fee_id)
    
    if request.method == 'POST':
        fee.is_paid = True
        fee.save()
        messages.success(request, f'Fee "{fee.name}" marked as paid successfully.')
        return redirect('myapp:individual_student_fees')
    
    context = {
        'fee': fee
    }
    return render(request, 'myapp/mark_fee_as_paid.html', context)

# ==================== ANALYTICS VIEWS ====================

@login_required
def payment_analytics_dashboard(request):
    """Comprehensive payment analytics dashboard"""
    from django.db.models import Sum, Count, Q
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    # Get filter parameters
    view_type = request.GET.get('view', 'school')  # school, class, batch, student, category
    student_id = request.GET.get('student')
    class_name = request.GET.get('class')
    batch_year = request.GET.get('batch')
    category_id = request.GET.get('category')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Set default date range (last 12 months)
    if not date_from:
        date_from = (timezone.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    if not date_to:
        date_to = timezone.now().strftime('%Y-%m-%d')
    
    # Base queryset for payments
    payments = Payment.objects.filter(
        payment_date__range=[date_from, date_to]
    ).select_related('student', 'fee_structure__category')
    
    # Apply filters based on view type
    if view_type == 'student' and student_id:
        payments = payments.filter(student_id=student_id)
    elif view_type == 'class' and class_name:
        payments = payments.filter(student__class_name=class_name)
    elif view_type == 'batch' and batch_year:
        payments = payments.filter(student__year_batch=batch_year)
    elif view_type == 'category' and category_id:
        payments = payments.filter(fee_structure__category_id=category_id)
    
    # Calculate statistics
    total_payments = payments.count()
    total_amount = payments.aggregate(total=Sum('amount'))['total'] or 0
    
    # Status breakdown
    status_breakdown = payments.values('status').annotate(
        count=Count('id'),
        total_amount=Sum('amount')
    ).order_by('status')
    
    # Monthly trend
    monthly_trend = payments.extra(
        select={'month': "EXTRACT(month FROM payment_date)"}
    ).values('month').annotate(
        count=Count('id'),
        total_amount=Sum('amount')
    ).order_by('month')
    
    # Category breakdown
    category_breakdown = payments.values(
        'fee_structure__category__name'
    ).annotate(
        count=Count('id'),
        total_amount=Sum('amount')
    ).order_by('-total_amount')
    
    # Payment method breakdown
    method_breakdown = payments.values('payment_method').annotate(
        count=Count('id'),
        total_amount=Sum('amount')
    ).order_by('-total_amount')
    
    # Get pending payments (FeeStatus records)
    pending_payments = FeeStatus.objects.filter(
        due_date__range=[date_from, date_to]
    ).select_related('student', 'fee_structure__category')
    
    # Apply same filters to pending payments
    if view_type == 'student' and student_id:
        pending_payments = pending_payments.filter(student_id=student_id)
    elif view_type == 'class' and class_name:
        pending_payments = pending_payments.filter(student__class_name=class_name)
    elif view_type == 'batch' and batch_year:
        pending_payments = pending_payments.filter(student__year_batch=batch_year)
    elif view_type == 'category' and category_id:
        pending_payments = pending_payments.filter(fee_structure__category_id=category_id)
    
    pending_total = pending_payments.filter(status='pending').count()
    pending_amount = pending_payments.filter(status='pending').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    overdue_total = pending_payments.filter(
        status='pending', 
        due_date__lt=timezone.now().date()
    ).count()
    overdue_amount = pending_payments.filter(
        status='pending', 
        due_date__lt=timezone.now().date()
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Get filter options
    students = Student.objects.filter(is_active=True).order_by('first_name')
    classes = Student.objects.values_list('class_name', flat=True).distinct().exclude(class_name='').order_by('class_name')
    batches = Student.objects.values_list('year_batch', flat=True).distinct().order_by('-year_batch')
    categories = FeeCategory.objects.filter(is_active=True).order_by('name')
    
    context = {
        'view_type': view_type,
        'student_id': student_id,
        'class_name': class_name,
        'batch_year': batch_year,
        'category_id': category_id,
        'date_from': date_from,
        'date_to': date_to,
        
        # Statistics
        'total_payments': total_payments,
        'total_amount': total_amount,
        'pending_total': pending_total,
        'pending_amount': pending_amount,
        'overdue_total': overdue_total,
        'overdue_amount': overdue_amount,
        
        # Breakdowns
        'status_breakdown': status_breakdown,
        'monthly_trend': monthly_trend,
        'category_breakdown': category_breakdown,
        'method_breakdown': method_breakdown,
        
        # Filter options
        'students': students,
        'classes': classes,
        'batches': batches,
        'categories': categories,
        
        # Detailed data
        'recent_payments': payments.order_by('-payment_date')[:10],
        'pending_payments_list': pending_payments.filter(status='pending').order_by('due_date')[:10],
        'overdue_payments_list': pending_payments.filter(
            status='pending', 
            due_date__lt=timezone.now().date()
        ).order_by('due_date')[:10],
    }
    
    return render(request, 'myapp/payment_analytics_dashboard.html', context)

@login_required
def payment_analytics_export(request):
    """Export payment analytics data"""
    from django.http import HttpResponse
    from django.db.models import Sum, Count
    import csv
    
    view_type = request.GET.get('view', 'school')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Get payments data
    payments = Payment.objects.filter(
        payment_date__range=[date_from, date_to]
    ).select_related('student', 'fee_structure__category')
    
    # Apply filters
    if view_type == 'student':
        student_id = request.GET.get('student')
        if student_id:
            payments = payments.filter(student_id=student_id)
    elif view_type == 'class':
        class_name = request.GET.get('class')
        if class_name:
            payments = payments.filter(student__class_name=class_name)
    elif view_type == 'batch':
        batch_year = request.GET.get('batch')
        if batch_year:
            payments = payments.filter(student__year_batch=batch_year)
    elif view_type == 'category':
        category_id = request.GET.get('category')
        if category_id:
            payments = payments.filter(fee_structure__category_id=category_id)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="payment_analytics_{view_type}_{date_from}_to_{date_to}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Student Name', 'Student ID', 'Class', 'Batch', 
        'Fee Category', 'Amount', 'Payment Date', 'Payment Method', 'Status'
    ])
    
    for payment in payments:
        writer.writerow([
            f"{payment.student.first_name} {payment.student.last_name}",
            payment.student.student_id,
            payment.student.class_name or '',
            payment.student.year_batch,
            payment.fee_structure.category.name if payment.fee_structure else 'Individual Fee',
            payment.amount,
            payment.payment_date,
            payment.payment_method,
            payment.status,
        ])
    
    return response