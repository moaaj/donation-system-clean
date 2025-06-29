from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile
from myapp.models import Student


class EnhancedUserCreationForm(UserCreationForm):
    """Enhanced user registration form with additional fields"""
    email = forms.EmailField(required=True, help_text='Required. Enter a valid email address.')
    first_name = forms.CharField(max_length=30, required=True, help_text='Required.')
    last_name = forms.CharField(max_length=30, required=True, help_text='Required.')
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
    """Registration form with role-based validation"""
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
        choices=[('admin', 'Admin'), ('student', 'Student')],
        required=True,
        help_text='Select your role.',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    student_id = forms.CharField(
        max_length=20, 
        required=False, 
        help_text='Required for students. Enter your unique student ID.',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., STU2024001'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        role = self.cleaned_data.get('role')
        
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already in use.')
        
        # Validate admin email format
        if role == 'admin' and not email.endswith('@admin.com'):
            raise forms.ValidationError('Admin email addresses must end with @admin.com')
        
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username
    
    def clean_student_id(self):
        student_id = self.cleaned_data.get('student_id')
        role = self.cleaned_data.get('role')
        
        if role == 'student':
            if not student_id:
                raise forms.ValidationError('Student ID is required for student registration.')
            
            # Check if student ID already exists
            if Student.objects.filter(student_id=student_id).exists():
                raise forms.ValidationError('This student ID is already registered.')
        
        return student_id
    
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        student_id = cleaned_data.get('student_id')
        
        # Additional validation for student role
        if role == 'student' and not student_id:
            self.add_error('student_id', 'Student ID is required for student registration.')
        
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