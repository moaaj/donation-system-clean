from rest_framework import serializers
from .models import Donor, Donation, Transaction

class DonorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Donor
        fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'address', 'date_joined']

class DonationSerializer(serializers.ModelSerializer):
    donor = DonorSerializer(read_only=True)  # Embed the donor data in the donation response
    class Meta:
        model = Donation
        fields = ['id', 'donor', 'amount', 'date', 'message', 'donation_method']

class TransactionSerializer(serializers.ModelSerializer):
    donation = DonationSerializer(read_only=True)  # Embed the donation data in the transaction response
    class Meta:
        model = Transaction
        fields = ['id', 'donation', 'transaction_id', 'transaction_date', 'status', 'amount']
