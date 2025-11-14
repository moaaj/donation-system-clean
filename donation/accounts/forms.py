from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile
from myapp.models import Student, FeeStructure


class EnhancedUserCreationForm(UserCreationForm):
    """Enhanced user registration form with additional fields"""
    email = forms.EmailField(required=True, help_text='Required. Enter a valid email address.')
    first_name = forms.CharField(max_length=30, required=True, help_text='Required.')
    last_name = forms.CharField(max_length=30, required=True, help_text='Optional.')
    phone_number = forms.CharField(max_length=15, required=False, help_text='Optional.')
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False, help_text='Optional.')
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}), help_text='Optional.')
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already in use.')
        
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username


class RoleBasedRegistrationForm(UserCreationForm):
    """Registration form with role-based validation and form selection for students"""
    email = forms.EmailField(
        required=True, 
        help_text='Required. Enter a valid email address.',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    first_name = forms.CharField(
        max_length=30, 
        required=True, 
        help_text='Required.',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True, 
        help_text='Required.',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    phone_number = forms.CharField(
        max_length=15, 
        required=False, 
        help_text='Optional.',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}), 
        required=False, 
        help_text='Optional.'
    )
    role = forms.ChoiceField(
        choices=[
            ('admin', 'Super Admin'),
            ('student', 'Student'),
            ('parent', 'Parent'),
            ('donation_admin', 'Donation Module Admin'),
            ('waqaf_admin', 'Waqaf Module Admin'),
            ('school_fees_admin', 'School Fees Module Admin'),
            ('school_fees_level_admin', 'School Fees Level Admin'),
        ],
        required=True,
        help_text='Select your role.',
        widget=forms.Select(attrs={'class': 'form-control', 'onchange': 'toggleRoleFields()'})
    )
    student_id = forms.CharField(
        max_length=20, 
        required=False, 
        help_text='Required for students. Enter your unique student ID.',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., STU2024001'})
    )
    # New field for form selection
    form_level = forms.ChoiceField(
        choices=[('', '-- Select Form --')],
        required=False,
        help_text='Required for students. Select your form level.',
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_form_level'})
    )
    
    # Level selection for school fees level admin
    admin_level = forms.ChoiceField(
        choices=[
            ('', '-- Select Level --'),
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
        ],
        required=False,
        help_text='Required for School Fees Level Admin. Select the level you will manage.',
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_admin_level', 'style': 'display: none;'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get available forms from FeeStructure
        try:
            available_forms = FeeStructure.objects.values_list('form', flat=True).distinct().order_by('form')
            form_choices = [('', '-- Select Form --')] + [(form, form) for form in available_forms]
            self.fields['form_level'].choices = form_choices
        except:
            # If FeeStructure is not available, provide default choices
            self.fields['form_level'].choices = [
                ('', '-- Select Form --'),
                ('Form 1', 'Form 1'),
                ('Form 2', 'Form 2'),
                ('Form 3', 'Form 3'),
                ('Form 4', 'Form 4'),
                ('Form 5', 'Form 5'),
            ]
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already in use.')
        
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username
    
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        student_id = cleaned_data.get('student_id')
        form_level = cleaned_data.get('form_level')
        admin_level = cleaned_data.get('admin_level')
        
        # Validate student-specific fields
        if role == 'student':
            if not student_id:
                raise forms.ValidationError("Student ID is required for student registration.")
            
            if not form_level:
                raise forms.ValidationError("Form level is required for student registration.")
            
            # Check if student ID already exists
            if Student.objects.filter(student_id=student_id).exists():
                raise forms.ValidationError("A student with this Student ID already exists.")
        
        # Validate school fees level admin fields
        if role == 'school_fees_level_admin':
            if not admin_level:
                raise forms.ValidationError("Admin level is required for School Fees Level Admin registration.")
        
        return cleaned_data


class EnhancedAuthenticationForm(AuthenticationForm):
    """Enhanced login form with remember me functionality"""
    remember_me = forms.BooleanField(required=False, initial=False)
    
    def clean(self):
        cleaned_data = super().clean()
        remember_me = cleaned_data.get('remember_me')
        if not remember_me:
            self.request.session.set_expiry(0)  # Session expires when browser closes
        return cleaned_data


class UserProfileForm(forms.ModelForm):
    """Form for updating user profile"""
    class Meta:
        model = UserProfile
        fields = ['phone_number', 'address', 'date_of_birth', 'profile_picture']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class PasswordChangeRequestForm(forms.Form):
    """Form for requesting password reset"""
    email = forms.EmailField(required=True, help_text='Enter the email address associated with your account.')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError('No user found with this email address.')
        return email


class PasswordResetForm(forms.Form):
    """Form for resetting password"""
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput,
        min_length=8,
        help_text="Password must be at least 8 characters long."
    )
    new_password2 = forms.CharField(
        label="Confirm new password",
        widget=forms.PasswordInput,
        min_length=8
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("Passwords don't match.")
        
        return cleaned_data 