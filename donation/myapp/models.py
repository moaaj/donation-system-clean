from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.core.files.base import ContentFile
import qrcode
from io import BytesIO
from django.core.files.base import File
from django.urls import reverse
from django.conf import settings
import random
import string

# At the top of your models.py
PAYMENT_METHODS = [
    ('cash', 'Cash'),
    ('bank_transfer', 'Bank Transfer'),
    ('online', 'Online Payment'),
]
PAYMENT_STATUS = [
    ('pending', 'Pending'),
    ('completed', 'Completed'),
    ('failed', 'Failed'),
]

class Student(models.Model):
    LEVEL_CHOICES = [
        ('year', 'Year'),
        ('form', 'Form'),
        ('standard', 'Standard'),
        ('others', 'Others'),
    ]
    
    student_id = models.CharField(max_length=20, unique=True)
    nric = models.CharField(max_length=12, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    class_name = models.CharField(max_length=50, blank=True, null=True, help_text="Student's class")
    program = models.CharField(max_length=100, blank=True, null=True, help_text="Student's program")
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, blank=True, null=True, help_text="Student's level (year/form/standard/others)")
    level_custom = models.CharField(max_length=50, blank=True, null=True, help_text="Custom level value when 'others' is selected")
    year_batch = models.IntegerField(null=True, blank=True)  # e.g., 2024
    phone_number = models.CharField(max_length=15, blank=True, null=True, help_text="Student's phone number")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.student_id})"
    
    def get_level_display_value(self):
        """Return the display value for level, including custom value if 'form' or 'others' is selected"""
        print(f"DEBUG: get_level_display_value called for student {self.id}")
        print(f"DEBUG: level={self.level}, level_custom={self.level_custom}")
        
        if self.level in ['form', 'others'] and self.level_custom:
            print(f"DEBUG: Returning level_custom: {self.level_custom}")
            return self.level_custom
        print(f"DEBUG: Returning get_level_display: {self.get_level_display()}")
        return self.get_level_display()

class Parent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nric = models.CharField(max_length=12, unique=True)
    phone_number = models.CharField(max_length=15)
    address = models.TextField()
    students = models.ManyToManyField(Student, related_name='parents')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()}"

class FeeCategory(models.Model):
    CATEGORY_TYPES = [
        ('general', 'General'),
        ('individual', 'Individual Student'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPES, default='general', help_text="General categories apply to all students, Individual categories are for specific students")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_category_type_display()})"

class IndividualStudentFee(models.Model):
    """Model for individual student-specific fees like overtime or demerit penalties"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='individual_fees')
    category = models.ForeignKey(FeeCategory, on_delete=models.CASCADE, limit_choices_to={'category_type': 'individual'})
    name = models.CharField(max_length=100, help_text="Name of the fee (e.g., Overtime Fee, Demerit Penalty)")
    description = models.TextField(help_text="Description of why this fee was applied")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_individual_fees')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Individual Student Fee'
        verbose_name_plural = 'Individual Student Fees'

    def __str__(self):
        return f"{self.student.first_name} {self.student.last_name} - {self.name} (RM {self.amount})"

    def is_overdue(self):
        """Check if the fee is overdue"""
        from django.utils import timezone
        return self.due_date < timezone.now().date() and not self.is_paid

    def get_status_display(self):
        """Get the status of the fee"""
        if self.is_paid:
            return "Paid"
        elif self.is_overdue():
            return "Overdue"
        else:
            return "Pending"

class FeeStructure(models.Model):
    category = models.ForeignKey(FeeCategory, on_delete=models.CASCADE)
    form = models.CharField(max_length=10, help_text="Form/grade level (e.g., Form 1, Form 2, Form 3)")
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    frequency = models.CharField(max_length=20, choices=[
        ('monthly', 'Monthly'),
        ('termly', 'Termly'),
        ('yearly', 'Yearly')
    ])
    # New fields for flexible monthly payments
    monthly_duration = models.IntegerField(
        choices=[(10, '10 months'), (11, '11 months'), (12, '12 months')],
        null=True, 
        blank=True,
        help_text="Number of months for monthly payment plan (only for monthly frequency)"
    )
    total_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Total amount to be paid over the monthly duration"
    )
    auto_generate_payments = models.BooleanField(
        default=False,
        help_text="Automatically generate monthly payment records for students"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['category', 'form']  # Ensure one fee structure per category per form
        ordering = ['category__name', 'form']

    def __str__(self):
        if self.frequency == 'monthly' and self.monthly_duration:
            return f"{self.category.name} - {self.form} ({self.frequency}, {self.monthly_duration} months)"
        return f"{self.category.name} - {self.form} ({self.frequency})"
    
    def get_monthly_amount(self):
        """Calculate monthly amount based on total amount and duration"""
        if self.frequency == 'monthly' and self.total_amount and self.monthly_duration:
            from decimal import Decimal, ROUND_HALF_UP
            monthly_amount = (self.total_amount / self.monthly_duration).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            return monthly_amount
        return self.amount or 0
    
    @classmethod
    def get_for_student(cls, student, category=None):
        """
        Get the appropriate fee structure for a student based on their form/grade level.
        This ensures all students in the same form pay the same amount.
        """
        # Get the student's form/grade level
        student_level = student.get_level_display_value()
        
        # Filter by student's level and optionally by category
        queryset = cls.objects.filter(
            form__iexact=student_level,  # Case-insensitive match
            is_active=True
        )
        
        if category:
            queryset = queryset.filter(category=category)
        
        return queryset.first()
    
    def generate_monthly_payments_for_student(self, student, start_date=None):
        """Generate monthly payment records for a specific student"""
        if not self.auto_generate_payments or self.frequency != 'monthly':
            return []
        
        if not start_date:
            from django.utils import timezone
            start_date = timezone.now().date()
        
        payments = []
        monthly_amount = self.get_monthly_amount()
        
        for month in range(self.monthly_duration):
            from datetime import timedelta
            due_date = start_date + timedelta(days=30 * month)
            
            # Create FeeStatus record
            fee_status = FeeStatus.objects.create(
                student=student,
                fee_structure=self,
                amount=monthly_amount,
                due_date=due_date,
                status='pending'
            )
            
            payments.append(fee_status)
        
        return payments

class Payment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS)
    receipt_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student} - {self.amount} - {self.payment_date}"

class PaymentReceipt(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE)
    receipt_file = models.FileField(upload_to='receipts/')
    generated_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Receipt for {self.payment}"

class Invoice(models.Model):
    INVOICE_STATUS = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    invoice_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='invoices')
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='invoice')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=INVOICE_STATUS, default='draft')
    notes = models.TextField(blank=True, null=True)
    terms_conditions = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.student}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Generate invoice number
            last_invoice = Invoice.objects.order_by('-id').first()
            if last_invoice:
                last_number = int(last_invoice.invoice_number.split('-')[1]) if '-' in last_invoice.invoice_number else 0
                self.invoice_number = f"INV-{last_number + 1:06d}"
            else:
                self.invoice_number = "INV-000001"
        
        # Calculate total amount - ensure both are Decimal
        from decimal import Decimal
        if isinstance(self.tax_amount, float):
            self.tax_amount = Decimal(str(self.tax_amount))
        if isinstance(self.amount, float):
            self.amount = Decimal(str(self.amount))
        self.total_amount = self.amount + self.tax_amount
        
        super().save(*args, **kwargs)
    
    def get_status_display_color(self):
        """Return Bootstrap color class for status"""
        status_colors = {
            'draft': 'secondary',
            'sent': 'info',
            'paid': 'success',
            'overdue': 'danger',
            'cancelled': 'warning',
        }
        return status_colors.get(self.status, 'secondary')
    
    def is_overdue(self):
        """Check if invoice is overdue"""
        return self.status == 'sent' and self.due_date < timezone.now().date()
    
    def mark_as_paid(self):
        """Mark invoice as paid"""
        self.status = 'paid'
        self.save()
    
    def send_invoice(self):
        """Mark invoice as sent"""
        self.status = 'sent'
        self.save()

class FeeDiscount(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE)
    discount_type = models.CharField(max_length=20, choices=[
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
        ('waiver', 'Full Waiver')
    ])
    value = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    valid_from = models.DateField()
    valid_to = models.DateField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student} - {self.discount_type} - {self.value}"

class PaymentReminder(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('paid', 'Paid')
    ])
    reminder_count = models.IntegerField(default=0)
    last_reminder_sent = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Reminder for {self.student} - {self.fee_structure}"

class SchoolBankAccount(models.Model):
    account_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50)
    bank_name = models.CharField(max_length=100)
    branch = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    fee_categories = models.ManyToManyField(FeeCategory)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"

class DonationCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class DonationEvent(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(DonationCategory, on_delete=models.CASCADE, related_name='events')
    qr_code = models.ImageField(upload_to='event_qrcodes/', blank=True, null=True)
    
    # File upload fields for donation event
    picture = models.ImageField(upload_to='donation_events/pictures/', blank=True, null=True, help_text="Upload a picture for the donation event")
    formal_letter = models.FileField(upload_to='donation_events/letters/', blank=True, null=True, help_text="Upload a formal letter document (PDF, DOC, etc.)")
    e_poster = models.ImageField(upload_to='donation_events/posters/', blank=True, null=True, help_text="Upload an e-poster for the donation event")
    
    # AI-related fields
    sentiment_score = models.FloatField(null=True, blank=True)
    sentiment_subjectivity = models.FloatField(null=True, blank=True)
    predicted_completion_rate = models.FloatField(null=True, blank=True)
    predicted_final_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estimated_days_to_completion = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.title

    def get_event_url(self):
        return reverse('donation_event_detail', args=[self.id])

    def generate_qr_code(self):
        print(f"[DEBUG] Generating QR code for event {self.id} ({self.title})")
        random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        qr = qrcode.make(random_str)
        buffer = BytesIO()
        qr.save(buffer, format='PNG')
        filename = f'event_{self.id}_qr.png'
        print(f"[DEBUG] Saving QR code to: {filename}")
        self.qr_code.save(filename, File(buffer), save=False)

    def save(self, *args, **kwargs):
        print(f"[DEBUG] Saving DonationEvent: {self.id} ({self.title})")
        super().save(*args, **kwargs)  # Save first to get an ID
        self.generate_qr_code()
        super().save(*args, **kwargs)  # Save again with QR code
        print(f"[DEBUG] DonationEvent saved: {self.id} ({self.title})")

    class Meta:
        ordering = ['-created_at']

class Donation(models.Model):
    PAYMENT_METHODS = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    event = models.ForeignKey(DonationEvent, on_delete=models.CASCADE, related_name='donations')
    donor_name = models.CharField(max_length=200)
    donor_email = models.EmailField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    message = models.TextField(blank=True, null=True, max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # AI-related fields
    fraud_probability = models.FloatField(null=True, blank=True)
    is_flagged = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    verification_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.donor_name} - {self.amount} - {self.event.title}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            self.event.current_amount += self.amount
            self.event.save()
        elif self.status == 'completed':
            self.event.current_amount += self.amount
            self.event.save()

# PIBG Muafakat Donation Models
class PibgDonationSettings(models.Model):
    """Settings for PIBG Muafakat donation feature"""
    banner_text = models.CharField(
        max_length=200,
        default="PIBG Muafakat Fund Donation",
        help_text="Banner text displayed above the donation section"
    )
    donation_message = models.TextField(
        default="Support our school's PIBG Muafakat fund to help improve facilities and student programs.",
        help_text="Message shown to users about the donation"
    )
    preset_amounts = models.JSONField(
        default=list,
        help_text="Preset donation amounts in RM"
    )
    is_mandatory = models.BooleanField(
        default=False,
        help_text="Whether donation selection is mandatory during checkout"
    )
    is_enabled = models.BooleanField(
        default=True,
        help_text="Whether the donation feature is enabled"
    )
    minimum_custom_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=5.00,
        help_text="Minimum amount for custom donations"
    )
    maximum_custom_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=1000.00,
        help_text="Maximum amount for custom donations"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "PIBG Donation Settings"
        verbose_name_plural = "PIBG Donation Settings"

    def __str__(self):
        return f"PIBG Donation Settings (Updated: {self.updated_at.strftime('%Y-%m-%d')})"

    @classmethod
    def get_settings(cls):
        """Get the current donation settings, create default if none exists"""
        settings, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'preset_amounts': [10, 20, 30, 50, 100],
                'donation_message': "Support our school's PIBG Muafakat fund to help improve facilities and student programs.",
                'is_mandatory': False,
                'is_enabled': True,
                'minimum_custom_amount': 5.00,
                'maximum_custom_amount': 1000.00,
            }
        )
        return settings

class PibgDonation(models.Model):
    """Model to track PIBG Muafakat donations"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='pibg_donations')
    parent = models.ForeignKey('Parent', on_delete=models.CASCADE, null=True, blank=True, related_name='pibg_donations')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='completed')
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    receipt_number = models.CharField(max_length=50, unique=True)
    
    # Link to the main payment if part of fee payment
    related_payment = models.ForeignKey('Payment', on_delete=models.CASCADE, null=True, blank=True, related_name='pibg_donations')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "PIBG Muafakat Donation"
        verbose_name_plural = "PIBG Muafakat Donations"

    def __str__(self):
        return f"PIBG Donation - {self.student.first_name} {self.student.last_name} - RM{self.amount}"

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            import time
            self.receipt_number = f'PIBG{timezone.now().strftime("%Y%m%d%H%M%S")}{int(time.time() * 1000000) % 1000:03d}'
        super().save(*args, **kwargs)

# Temporary placeholder models to prevent migration issues
class ParentCart(models.Model):
    parent = models.OneToOneField('Parent', on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Parent Cart'
        verbose_name_plural = 'Parent Carts'

class ParentCartItem(models.Model):
    cart = models.ForeignKey(ParentCart, on_delete=models.CASCADE, related_name='items')
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    fee_structure = models.ForeignKey('FeeStructure', on_delete=models.CASCADE, null=True, blank=True)
    individual_fee = models.ForeignKey('IndividualStudentFee', on_delete=models.CASCADE, null=True, blank=True)
    fee_status = models.ForeignKey('FeeStatus', on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'
        unique_together = ('cart', 'student', 'fee_structure', 'individual_fee', 'fee_status')

class ParentPaymentHistory(models.Model):
    parent = models.ForeignKey('Parent', on_delete=models.CASCADE, related_name='payment_history')
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    payment = models.ForeignKey('Payment', on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=200)

    class Meta:
        verbose_name = 'Parent Payment History'
        verbose_name_plural = 'Parent Payment Histories'
        ordering = ['-payment_date']

class EmailPreferences(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email_address = models.EmailField()
    receive_payment_receipts = models.BooleanField(default=True)
    receive_payment_reminders = models.BooleanField(default=True)
    receive_monthly_statements = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Email preferences for {self.user.username}"

class FeeStatus(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('overdue', 'Overdue'),
        ('paid', 'Paid'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_statuses')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-due_date']
        verbose_name_plural = 'Fee Statuses'
    
    def __str__(self):
        return f"{self.student.first_name} {self.student.last_name} - {self.fee_structure.category.name} - {self.amount}"
    
    def is_overdue(self):
        return self.due_date < timezone.now().date() and self.status != 'paid'
    
    def update_status(self):
        if self.status != 'paid':
            if self.is_overdue():
                self.status = 'overdue'
            else:
                self.status = 'pending'
            self.save()
    
    def save(self, *args, **kwargs):
        """Ensure the amount is always consistent with the fee structure for the student's form level"""
        if self.fee_structure:
            # Get the correct amount from the fee structure for this student's form level
            student_level = self.student.get_level_display_value()
            if self.fee_structure.form.lower() == student_level.lower():
                # Use the fee structure amount to ensure consistency
                if self.fee_structure.frequency == 'monthly' and self.fee_structure.monthly_duration:
                    self.amount = self.fee_structure.get_monthly_amount()
                else:
                    self.amount = self.fee_structure.amount or 0
        super().save(*args, **kwargs)
    
    def get_original_amount(self):
        """Get the original fee amount before any discounts"""
        return self.amount
    
    def get_discounted_amount(self):
        """Calculate the discounted amount based on approved waivers"""
        from django.utils import timezone
        today = timezone.now().date()
        
        # Get all active approved waivers for this student and fee category
        active_waivers = FeeWaiver.objects.filter(
            student=self.student,
            category=self.fee_structure.category,
            status='approved',
            start_date__lte=today,
            end_date__gte=today
        )
        
        if not active_waivers.exists():
            return self.amount
        
        # Calculate total discount
        total_discount = 0
        original_amount = self.amount
        
        for waiver in active_waivers:
            if waiver.percentage:
                # Percentage-based discount
                discount_amount = (original_amount * waiver.percentage) / 100
                total_discount += discount_amount
            else:
                # Fixed amount discount
                total_discount += waiver.amount
        
        # Ensure discount doesn't exceed original amount
        discounted_amount = max(0, original_amount - total_discount)
        return discounted_amount
    
    def get_discount_info(self):
        """Get information about applied discounts"""
        from django.utils import timezone
        today = timezone.now().date()
        
        active_waivers = FeeWaiver.objects.filter(
            student=self.student,
            category=self.fee_structure.category,
            status='approved',
            start_date__lte=today,
            end_date__gte=today
        )
        
        discount_info = {
            'has_discount': False,
            'original_amount': self.amount,
            'discounted_amount': self.amount,
            'total_discount': 0,
            'waivers': []
        }
        
        if active_waivers.exists():
            discount_info['has_discount'] = True
            total_discount = 0
            
            for waiver in active_waivers:
                waiver_info = {
                    'type': waiver.get_waiver_type_display(),
                    'reason': waiver.reason,
                    'amount': waiver.amount,
                    'percentage': waiver.percentage,
                    'discount_amount': waiver.calculate_discount_amount(self.amount)
                }
                discount_info['waivers'].append(waiver_info)
                
                if waiver.percentage:
                    total_discount += (self.amount * waiver.percentage) / 100
                else:
                    total_discount += waiver.amount
            
            discount_info['total_discount'] = total_discount
            discount_info['discounted_amount'] = max(0, self.amount - total_discount)
        
        return discount_info

class FeeWaiver(models.Model):
    WAIVER_TYPES = [
        ('scholarship', 'Scholarship'),
        ('discount', 'Discount'),
        ('waiver', 'Fee Waiver'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_waivers', null=True, blank=True)
    waiver_type = models.CharField(max_length=20, choices=WAIVER_TYPES)
    category = models.ForeignKey(FeeCategory, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    reason = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approved_waivers')
    approved_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_waiver_type_display()} - {self.reason[:50]}"
    
    def is_active(self):
        today = timezone.now().date()
        return (self.status == 'approved' and 
                self.start_date <= today <= self.end_date)
    
    def calculate_discount_amount(self, original_amount):
        if self.percentage:
            return (original_amount * self.percentage) / 100
        return self.amount
    
    class Meta:
        ordering = ['-created_at']

class FeeSettings(models.Model):
    fee_mode = models.CharField(
        max_length=10,
        choices=[
            ('term', 'Term-based Collection'),
            ('annual', 'Annual Collection')
        ],
        default='term'
    )
    due_date = models.IntegerField(
        choices=[(1, '1st'), (5, '5th'), (10, '10th'), (15, '15th')],
        default=10
    )
    grace_period = models.IntegerField(
        default=5,
        help_text='Number of days after due date before late penalty applies'
    )
    late_penalty = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text='Percentage of late payment penalty'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Fee Setting'
        verbose_name_plural = 'Fee Settings'

    def __str__(self):
        return f"Fee Settings ({self.get_fee_mode_display()})"

class AcademicTerm(models.Model):
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Academic Term'
        verbose_name_plural = 'Academic Terms'

    def __str__(self):
        return self.name

    def is_current(self):
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date

class UserProfile(models.Model):
    """Extended user profile with role-based access"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='myapp_profile')
    role = models.CharField(
        choices=[
            ('admin', 'Super Admin'), 
            ('student', 'Student'), 
            ('parent', 'Parent'),
            ('donation_admin', 'Donation Module Admin'),
            ('waqaf_admin', 'Waqaf Module Admin'),
            ('school_fees_admin', 'School Fees Module Admin'),
            ('school_fees_level_admin', 'School Fees Level Admin'),
        ], 
        default='student', 
        max_length=30
    )
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='user_profile', null=True, blank=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.username}'s Profile ({self.role})"

    def is_admin(self):
        return self.role == 'admin'

    def is_student(self):
        return self.role == 'student'

    def is_parent(self):
        return self.role == 'parent'
    
    def is_donation_admin(self):
        return self.role == 'donation_admin'
    
    def is_waqaf_admin(self):
        return self.role == 'waqaf_admin'
    
    def is_school_fees_admin(self):
        return self.role == 'school_fees_admin'
    
    def is_school_fees_level_admin(self):
        return self.role == 'school_fees_level_admin'
    
    def is_module_admin(self):
        """Check if user is any type of module admin"""
        return self.role in ['donation_admin', 'waqaf_admin', 'school_fees_admin', 'school_fees_level_admin']
    
    def is_form1_admin(self):
        """Check if user is Form 1 admin"""
        if self.role == 'school_fees_level_admin':
            return self.level_assignments.filter(level='form1').exists()
        return False
    
    def is_form3_admin(self):
        """Check if user is Form 3 admin"""
        if self.role == 'school_fees_level_admin':
            return self.level_assignments.filter(level='form3').exists()
        return False
    
    def get_assigned_levels(self):
        """Get all levels assigned to this user"""
        if self.role == 'school_fees_level_admin':
            return [assignment.level for assignment in self.level_assignments.all()]
        return []


class ModulePermission(models.Model):
    """Model for module-specific permissions"""
    MODULE_CHOICES = [
        ('donation', 'Donation Module'),
        ('waqaf', 'Waqaf Module'),
        ('school_fees', 'School Fees Module'),
        ('pibg_donation', 'PIBG Donation'),
    ]
    
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='module_permissions')
    module = models.CharField(max_length=20, choices=MODULE_CHOICES)
    can_view = models.BooleanField(default=True)
    can_add = models.BooleanField(default=False)
    can_change = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_manage_settings = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user_profile', 'module')
        verbose_name = 'Module Permission'
        verbose_name_plural = 'Module Permissions'
    
    def __str__(self):
        return f"{self.user_profile.user.username} - {self.get_module_display()}"


class SchoolFeesLevelAdmin(models.Model):
    """Model for school fees level-specific admin assignments"""
    LEVEL_CHOICES = [
        ('form1', 'Form 1'),
        ('form2', 'Form 2'),
        ('form3', 'Form 3'),
        ('form4', 'Form 4'),
        ('form5', 'Form 5'),
        ('year1', 'Year 1'),
        ('year2', 'Year 2'),
        ('year3', 'Year 3'),
        ('year4', 'Year 4'),
        ('year5', 'Year 5'),
        ('standard1', 'Standard 1'),
        ('standard2', 'Standard 2'),
        ('standard3', 'Standard 3'),
        ('standard4', 'Standard 4'),
        ('standard5', 'Standard 5'),
        ('standard6', 'Standard 6'),
        ('all', 'All Levels'),
    ]
    
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='level_assignments')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    can_view = models.BooleanField(default=True)
    can_add = models.BooleanField(default=False)
    can_change = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_manage_fees = models.BooleanField(default=False)
    can_manage_payments = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user_profile', 'level')
        verbose_name = 'School Fees Level Admin'
        verbose_name_plural = 'School Fees Level Admins'
    
    def __str__(self):
        return f"{self.user_profile.user.username} - {self.get_level_display()}"


class PredefinedDonationAmount(models.Model):
    """Model for admin-configurable predefined donation amounts"""
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Donation amount")
    is_active = models.BooleanField(default=True, help_text="Whether this amount is available for selection")
    display_order = models.PositiveIntegerField(default=0, help_text="Order in which amounts are displayed")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'amount']
        verbose_name = 'Predefined Donation Amount'
        verbose_name_plural = 'Predefined Donation Amounts'

    def __str__(self):
        return f"RM{self.amount}"

    def formatted_amount(self):
        return f"RM{self.amount:,.2f}"




