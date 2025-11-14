from django import forms
from myapp.models import Donation, DonationCategory, DonationEvent

class DonationForm(forms.ModelForm):
    class Meta:
        model = Donation
        fields = ['event', 'donor_name', 'donor_email', 'amount', 'payment_method', 'message']
        widgets = {
            'event': forms.Select(attrs={'class': 'form-control'}),
            'donor_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your name'}),
            'donor_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter amount', 'min': '1', 'step': '0.01'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('', 'Select payment method'),
                ('credit_card', 'Credit Card'),
                ('debit_card', 'Debit Card'),
                ('bank_transfer', 'Bank Transfer'),
            ]),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your message (optional)',
                'rows': 4,
                'maxlength': '200'
            }),
        }

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
        fields = ['title', 'description', 'category', 'start_date', 'end_date', 'target_amount', 'is_active', 'picture', 'formal_letter', 'e_poster']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'target_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'picture': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'formal_letter': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
            'e_poster': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
