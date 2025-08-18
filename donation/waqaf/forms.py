from django import forms
from .models import Contributor, Contribution, WaqafAsset

class ContributorForm(forms.ModelForm):
    class Meta:
        model = Contributor
        fields = ['name', 'email', 'phone', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
        }

class WaqafContributionForm(forms.ModelForm):
    class Meta:
        model = Contribution
        fields = ['asset', 'number_of_slots', 'dedicated_for', 'payment_type', 'payment_schedule', 'total_payments', 'auto_generate_payments']
        widgets = {
            'asset': forms.Select(attrs={'class': 'form-control'}),
            'number_of_slots': forms.NumberInput(attrs={'class': 'form-control'}),
            'dedicated_for': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_type': forms.Select(attrs={'class': 'form-control'}),
            'payment_schedule': forms.Select(attrs={'class': 'form-control'}),
            'total_payments': forms.NumberInput(attrs={'class': 'form-control'}),
            'auto_generate_payments': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get available assets with slot prices
        available_assets = WaqafAsset.objects.filter(slots_available__gt=0)
        choices = [(asset.id, f"{asset.name} - RM{asset.slot_price}/slot ({asset.slots_available} slots available)") 
                  for asset in available_assets]
        self.fields['asset'].choices = [('', 'Select an asset...')] + choices

    def clean(self):
        cleaned_data = super().clean()
        payment_type = cleaned_data.get('payment_type')
        total_payments = cleaned_data.get('total_payments')
        
        if payment_type == 'RECURRING' and total_payments <= 1:
            raise forms.ValidationError("Recurring payments must have more than 1 payment.")
        
        return cleaned_data

class WaqafAssetForm(forms.ModelForm):
    class Meta:
        model = WaqafAsset
        fields = ['name', 'description', 'current_value', 'target_amount', 'total_slots']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter asset name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter asset description'}),
            'current_value': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Current market value'}),
            'target_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Total amount needed'}),
            'total_slots': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Number of slots to sell'}),
        }
        labels = {
            'name': 'Asset Name',
            'description': 'Description',
            'current_value': 'Current Market Value (RM)',
            'target_amount': 'Target Amount (RM)',
            'total_slots': 'Total Slots',
        }

    def clean(self):
        cleaned_data = super().clean()
        target_amount = cleaned_data.get('target_amount')
        total_slots = cleaned_data.get('total_slots')
        
        if target_amount and total_slots:
            if target_amount <= 0:
                raise forms.ValidationError("Target amount must be greater than 0.")
            if total_slots <= 0:
                raise forms.ValidationError("Total slots must be greater than 0.")
        
        return cleaned_data
