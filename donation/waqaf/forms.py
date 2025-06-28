from django import forms
from .models import WaqafAsset, Contributor, FundDistribution, Contribution

class WaqafAssetForm(forms.ModelForm):
    class Meta:
        model = WaqafAsset
        fields = '__all__'

class ContributorForm(forms.ModelForm):
    class Meta:
        model = Contributor
        fields = ['name', 'email', 'phone', 'address']

class FundDistributionForm(forms.ModelForm):
    class Meta:
        model = FundDistribution
        fields = '__all__'

class WaqafContributionForm(forms.ModelForm):
    class Meta:
        model = Contribution
        fields = ['asset', 'number_of_slots', 'dedicated_for', 'payment_type']
        widgets = {
            'asset': forms.Select(attrs={'class': 'form-control'}),
            'number_of_slots': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Enter number of slots'
            }),
            'dedicated_for': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'E.g. For late mother, father, etc.'
            }),
            'payment_type': forms.RadioSelect(choices=Contribution.PAYMENT_TYPE_CHOICES)
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show assets with available slots
        available_assets = WaqafAsset.objects.filter(slots_available__gt=0)
        self.fields['asset'].queryset = available_assets
        
        # Customize the asset field
        self.fields['asset'].widget.attrs.update({
            'class': 'form-control'
        })
        
        # Add data attributes to each option
        choices = []
        for asset in available_assets:
            choices.append((
                asset.id,
                f"{asset.name} ({asset.slots_available} slots available)"
            ))
        self.fields['asset'].widget.choices = choices

    def clean_number_of_slots(self):
        number_of_slots = self.cleaned_data['number_of_slots']
        asset = self.cleaned_data.get('asset')
        
        if asset and number_of_slots > asset.slots_available:
            raise forms.ValidationError(
                f'Only {asset.slots_available} slots available for this asset.'
            )
        return number_of_slots
