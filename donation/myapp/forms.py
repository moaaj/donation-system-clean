from django import forms
from .models import (
    Student, Parent, FeeCategory, FeeStructure, Payment,
    FeeDiscount, PaymentReminder, SchoolBankAccount, DonationCategory, DonationEvent, Donation, PAYMENT_STATUS, FeeWaiver, IndividualStudentFee
)
import calendar
from django.urls import reverse
from django.conf import settings
import qrcode
from io import BytesIO
from django.core.files.base import File

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['student_id', 'nric', 'first_name', 'last_name', 'class_name', 'program', 'level', 'level_custom', 'year_batch', 'is_active']
        widgets = {
            'student_id': forms.TextInput(attrs={'class': 'form-control'}),
            'nric': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'class_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter class name'}),
            'program': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter program name'}),
            'level': forms.Select(attrs={'class': 'form-control'}),
            'level_custom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter custom level'}),
            'year_batch': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        level = cleaned_data.get('level')
        level_custom = cleaned_data.get('level_custom')
        
        # If level is 'others', level_custom is required
        if level == 'others' and not level_custom:
            raise forms.ValidationError("Custom level is required when 'Others' is selected.")
        
        # If level is not 'others', clear level_custom
        if level != 'others':
            cleaned_data['level_custom'] = None
            
        return cleaned_data

class ParentForm(forms.ModelForm):
    class Meta:
        model = Parent
        fields = ['nric', 'phone_number', 'address', 'students']
        widgets = {
            'nric': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'students': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }

class FeeCategoryForm(forms.ModelForm):
    class Meta:
        model = FeeCategory
        fields = ['name', 'description', 'category_type']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category_type': forms.Select(attrs={'class': 'form-control'}),
        }

class IndividualStudentFeeForm(forms.ModelForm):
    class Meta:
        model = IndividualStudentFee
        fields = ['student', 'category', 'name', 'description', 'amount', 'due_date']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Overtime Fee, Demerit Penalty'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Explain why this fee is being applied'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show individual student categories
        self.fields['category'].queryset = FeeCategory.objects.filter(category_type='individual', is_active=True)

class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = ['category', 'form', 'amount', 'frequency', 'monthly_duration', 'total_amount', 'auto_generate_payments']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'form': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter form (e.g., Form 1, Form 2)'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'frequency': forms.Select(attrs={'class': 'form-control'}),
            'monthly_duration': forms.Select(attrs={'class': 'form-control'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'auto_generate_payments': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show general categories for fee structures
        self.fields['category'].queryset = FeeCategory.objects.filter(category_type='general', is_active=True)
        
        # Add help text for new fields
        self.fields['monthly_duration'].help_text = "Select number of months for monthly payment plan"
        self.fields['total_amount'].help_text = "Total amount to be paid over the monthly duration"
        self.fields['auto_generate_payments'].help_text = "Automatically generate monthly payment records for students"
    
    def clean(self):
        cleaned_data = super().clean()
        frequency = cleaned_data.get('frequency')
        monthly_duration = cleaned_data.get('monthly_duration')
        total_amount = cleaned_data.get('total_amount')
        amount = cleaned_data.get('amount')
        
        print(f"DEBUG: Form clean - frequency={frequency}, monthly_duration={monthly_duration}, total_amount={total_amount}, amount={amount}")
        
        # If frequency is monthly, validate monthly_duration and total_amount
        if frequency == 'monthly':
            if not monthly_duration:
                raise forms.ValidationError("Monthly duration is required for monthly frequency.")
            if not total_amount:
                raise forms.ValidationError("Total amount is required for monthly frequency.")
            if total_amount <= 0:
                raise forms.ValidationError("Total amount must be greater than zero.")
            
            # Calculate and set the monthly amount
            from decimal import Decimal, ROUND_HALF_UP
            monthly_amount = (total_amount / monthly_duration).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            cleaned_data['amount'] = monthly_amount
            print(f"DEBUG: Calculated monthly amount: {monthly_amount}")
            
            # Clear monthly-specific fields if not monthly
            cleaned_data['auto_generate_payments'] = cleaned_data.get('auto_generate_payments', False)
        
        # If frequency is not monthly, validate regular amount
        else:
            if not amount or amount <= 0:
                raise forms.ValidationError("Amount is required and must be greater than zero for non-monthly frequencies.")
            # Clear monthly-specific fields
            cleaned_data['monthly_duration'] = None
            cleaned_data['total_amount'] = None
            cleaned_data['auto_generate_payments'] = False
        
        return cleaned_data

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['student', 'fee_structure', 'amount', 'payment_method', 'payment_date']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'fee_structure': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class FeeDiscountForm(forms.ModelForm):
    class Meta:
        model = FeeDiscount
        fields = ['student', 'fee_structure', 'discount_type', 'value', 'reason', 'valid_from', 'valid_to']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'fee_structure': forms.Select(attrs={'class': 'form-control'}),
            'discount_type': forms.Select(attrs={'class': 'form-control'}),
            'value': forms.NumberInput(attrs={'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'valid_from': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'valid_to': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class SchoolBankAccountForm(forms.ModelForm):
    class Meta:
        model = SchoolBankAccount
        fields = ['account_name', 'account_number', 'bank_name', 'branch', 'fee_categories']
        widgets = {
            'account_name': forms.TextInput(attrs={'class': 'form-control'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control'}),
            'branch': forms.TextInput(attrs={'class': 'form-control'}),
            'fee_categories': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }

class PaymentSearchForm(forms.Form):
    student = forms.ModelChoiceField(
        queryset=Student.objects.all(),
        required=False,
        empty_label="All Students",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    month = forms.ChoiceField(
        choices=[('', 'All Months')] + [(i, calendar.month_name[i]) for i in range(1, 13)],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    year = forms.ChoiceField(
        choices=[('', 'All Years')] + [(i, i) for i in range(2020, 2030)],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + PAYMENT_STATUS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class DonationCategoryForm(forms.ModelForm):
    class Meta:
        model = DonationCategory
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class DonationEventForm(forms.ModelForm):
    class Meta:
        model = DonationEvent
        fields = ['category', 'title', 'description', 'target_amount', 'start_date', 'end_date', 'is_active', 'picture', 'formal_letter', 'e_poster']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'picture': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'formal_letter': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
            'e_poster': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

class DonationForm(forms.ModelForm):
    class Meta:
        model = Donation
        fields = ['donor_name', 'donor_email', 'amount', 'payment_method']
        widgets = {
            'donor_name': forms.TextInput(attrs={'class': 'form-control'}),
            'donor_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
        }

class FeeWaiverForm(forms.ModelForm):
    student_name = forms.CharField(
        label='Student Name',
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter student name'
        })
    )
    student_class = forms.CharField(
        label='Student Class',
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter student class'
        })
    )
    student_id = forms.CharField(
        label='Student ID',
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter student ID'
        })
    )
    category = forms.CharField(
        label='Fee Category',
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter fee category (e.g., Tuition, Library, Sports)'
        })
    )

    class Meta:
        model = FeeWaiver
        fields = ['waiver_type', 'amount', 'percentage', 'reason', 'start_date', 'end_date']
        widgets = {
            'waiver_type': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter amount'}),
            'percentage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter percentage'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter reason for waiver'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get('amount')
        percentage = cleaned_data.get('percentage')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        # Validate amount or percentage
        if not amount and not percentage:
            raise forms.ValidationError("Please provide either an amount or a percentage.")
        if amount and percentage:
            raise forms.ValidationError("Please provide either an amount or a percentage, not both.")

        # Validate dates
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("End date must be after start date.")

        return cleaned_data

def get_event_url(self):
    return reverse('donation_event_detail', args=[self.id])

def generate_qr_code(self):
    path = self.get_event_url()
    url = f"{settings.SITE_DOMAIN}{path}"
    qr = qrcode.make(url)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    filename = f'event_{self.id}_qr.png'
    self.qr_code.save(filename, File(buffer), save=False) 