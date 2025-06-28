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
    student_id = models.CharField(max_length=20, unique=True)
    nric = models.CharField(max_length=12, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    year_batch = models.IntegerField()  # e.g., 2024
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.student_id})"

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
    name = models.CharField(max_length=100)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class FeeStructure(models.Model):
    category = models.ForeignKey(FeeCategory, on_delete=models.CASCADE)
    form = models.CharField(max_length=10)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    frequency = models.CharField(max_length=20, choices=[
        ('monthly', 'Monthly'),
        ('termly', 'Termly'),
        ('yearly', 'Yearly')
    ])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.category.name} - {self.form} ({self.frequency})"

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
        ('cash', 'Cash'),
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
        return f"{self.name} ({self.start_date.year})"

    def is_current(self):
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date
