from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import (
    UserProfile, ModulePermission, SchoolFeesLevelAdmin, Student, Parent, 
    FeeCategory, FeeStructure, Payment, FeeDiscount, SchoolBankAccount,
    DonationCategory, DonationEvent, IndividualStudentFee, FeeWaiver,
    PAYMENT_METHODS, PAYMENT_STATUS
)

class EnhancedUserCreationForm(UserCreationForm):
    """Enhanced user creation form with module-specific roles"""
    
    # Basic user fields
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    # Role selection
    ROLE_CHOICES = [
        ('admin', 'Super Admin'),
        ('student', 'Student'),
        ('parent', 'Parent'),
        ('donation_admin', 'Donation Module Admin'),
        ('waqaf_admin', 'Waqaf Module Admin'),
        ('school_fees_admin', 'School Fees Module Admin'),
        ('school_fees_level_admin', 'School Fees Level Admin'),
    ]
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control', 'onchange': 'toggleLevelField()'})
    )
    
    # Level selection for school fees level admin
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
    
    level = forms.ChoiceField(
        choices=LEVEL_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'style': 'display: none;'})
    )
    
    # Module permissions
    MODULE_CHOICES = [
        ('donation', 'Donation Module'),
        ('waqaf', 'Waqaf Module'),
        ('school_fees', 'School Fees Module'),
        ('pibg_donation', 'PIBG Donation'),
    ]
    
    modules = forms.MultipleChoiceField(
        choices=MODULE_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    
    # Permission checkboxes
    can_view = forms.BooleanField(required=False, initial=True)
    can_add = forms.BooleanField(required=False)
    can_change = forms.BooleanField(required=False)
    can_delete = forms.BooleanField(required=False)
    can_manage_settings = forms.BooleanField(required=False)
    can_manage_fees = forms.BooleanField(required=False)
    can_manage_payments = forms.BooleanField(required=False)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['first_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['last_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.is_staff = True  # All created users are staff
        
        if commit:
            user.save()
            
            # Create user profile
            profile = UserProfile.objects.create(
                user=user,
                role=self.cleaned_data['role']
            )
            
            # Set up module permissions
            if self.cleaned_data['modules']:
                for module in self.cleaned_data['modules']:
                    ModulePermission.objects.create(
                        user_profile=profile,
                        module=module,
                        can_view=self.cleaned_data['can_view'],
                        can_add=self.cleaned_data['can_add'],
                        can_change=self.cleaned_data['can_change'],
                        can_delete=self.cleaned_data['can_delete'],
                        can_manage_settings=self.cleaned_data['can_manage_settings']
                    )
            
            # Set up level-specific permissions for school fees level admin
            if self.cleaned_data['role'] == 'school_fees_level_admin' and self.cleaned_data['level']:
                SchoolFeesLevelAdmin.objects.create(
                    user_profile=profile,
                    level=self.cleaned_data['level'],
                    can_view=self.cleaned_data['can_view'],
                    can_add=self.cleaned_data['can_add'],
                    can_change=self.cleaned_data['can_change'],
                    can_delete=self.cleaned_data['can_delete'],
                    can_manage_fees=self.cleaned_data['can_manage_fees'],
                    can_manage_payments=self.cleaned_data['can_manage_payments']
                )
        
        return user


class ModulePermissionForm(forms.ModelForm):
    """Form for editing module permissions"""
    
    class Meta:
        model = ModulePermission
        fields = '__all__'
        widgets = {
            'user_profile': forms.Select(attrs={'class': 'form-control'}),
            'module': forms.Select(attrs={'class': 'form-control'}),
        }


class SchoolFeesLevelAdminForm(forms.ModelForm):
    """Form for editing school fees level admin permissions"""
    
    class Meta:
        model = SchoolFeesLevelAdmin
        fields = '__all__'
        widgets = {
            'user_profile': forms.Select(attrs={'class': 'form-control'}),
            'level': forms.Select(attrs={'class': 'form-control'}),
        }


# Basic Model Forms
class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = '__all__'
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'student_id': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'class_name': forms.TextInput(attrs={'class': 'form-control'}),
            'program': forms.TextInput(attrs={'class': 'form-control'}),
            'level': forms.Select(attrs={'class': 'form-control'}),
            'year_batch': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class ParentForm(forms.ModelForm):
    class Meta:
        model = Parent
        fields = '__all__'
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class FeeCategoryForm(forms.ModelForm):
    class Meta:
        model = FeeCategory
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'class_name': forms.TextInput(attrs={'class': 'form-control'}),
            'program': forms.TextInput(attrs={'class': 'form-control'}),
            'level': forms.Select(attrs={'class': 'form-control'}),
        }


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = '__all__'
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'transaction_id': forms.TextInput(attrs={'class': 'form-control'}),
        }


class CashPaymentForm(forms.ModelForm):
    """Form for recording cash payments made by parents at the school office"""
    
    class Meta:
        model = Payment
        fields = ['student', 'fee_structure', 'amount', 'payment_date', 'receipt_number']
        widgets = {
            'student': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'fee_structure': forms.Select(attrs={
                'class': 'form-control',
                'required': False
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01',
                'min': '0.01',
                'required': True
            }),
            'payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'receipt_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Auto-generated if left empty'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter students to show active ones only
        self.fields['student'].queryset = Student.objects.filter(is_active=True).order_by('first_name', 'last_name')
        
        # Filter fee structures to show active ones only
        self.fields['fee_structure'].queryset = FeeStructure.objects.filter(is_active=True).order_by('category__name', 'form')
        self.fields['fee_structure'].empty_label = "Select Fee Structure (Optional for individual fees)"
        
        # Set default payment date to today
        from django.utils import timezone
        if not self.instance.pk:
            self.fields['payment_date'].initial = timezone.now().date()
    
    def save(self, commit=True):
        payment = super().save(commit=False)
        
        # Set payment method to cash
        payment.payment_method = 'cash'
        payment.status = 'completed'
        
        # Generate receipt number if not provided
        if not payment.receipt_number:
            import time
            from django.utils import timezone
            payment.receipt_number = f'CASH{timezone.now().strftime("%Y%m%d%H%M%S")}{int(time.time() * 1000000) % 1000:03d}'
        
        if commit:
            payment.save()
            
            # Update related fee status if applicable
            if payment.fee_structure:
                from .models import FeeStatus
                try:
                    fee_status = FeeStatus.objects.get(
                        student=payment.student,
                        fee_structure=payment.fee_structure,
                        status__in=['pending', 'overdue']
                    )
                    fee_status.status = 'paid'
                    fee_status.save()
                except FeeStatus.DoesNotExist:
                    pass  # No matching fee status found
        
        return payment


class FeeDiscountForm(forms.ModelForm):
    class Meta:
        model = FeeDiscount
        fields = '__all__'
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'discount_type': forms.Select(attrs={'class': 'form-control'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class SchoolBankAccountForm(forms.ModelForm):
    class Meta:
        model = SchoolBankAccount
        fields = '__all__'
        widgets = {
            'account_name': forms.TextInput(attrs={'class': 'form-control'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control'}),
            'bank_code': forms.TextInput(attrs={'class': 'form-control'}),
        }


class DonationCategoryForm(forms.ModelForm):
    class Meta:
        model = DonationCategory
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class DonationEventForm(forms.ModelForm):
    class Meta:
        model = DonationEvent
        fields = '__all__'
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'target_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class DonationForm(forms.ModelForm):
    class Meta:
        model = Payment  # Assuming donations are tracked as payments
        fields = ['amount', 'payment_method', 'receipt_number']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'receipt_number': forms.TextInput(attrs={'class': 'form-control'}),
        }


class IndividualStudentFeeForm(forms.ModelForm):
    class Meta:
        model = IndividualStudentFee
        fields = '__all__'
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'fee_category': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_paid': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class FeeWaiverForm(forms.ModelForm):
    class Meta:
        model = FeeWaiver
        fields = '__all__'
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'fee_category': forms.Select(attrs={'class': 'form-control'}),
            'waiver_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


# Search Forms
class PaymentSearchForm(forms.Form):
    student = forms.ModelChoiceField(
        queryset=Student.objects.filter(is_active=True).order_by('first_name', 'last_name'),
        required=False,
        empty_label="All Students",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by student name, ID, or payment method...'
        })
    )
    payment_method = forms.ChoiceField(
        choices=[('', 'All Methods')] + PAYMENT_METHODS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + PAYMENT_STATUS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    month = forms.ChoiceField(
        choices=[('', 'All Months')] + [(i, f'{i:02d}') for i in range(1, 13)],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    year = forms.ChoiceField(
        choices=[('', 'All Years')] + [(i, str(i)) for i in range(2020, 2030)],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )