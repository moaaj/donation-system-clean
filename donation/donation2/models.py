from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.files.base import ContentFile
import qrcode
from io import BytesIO
from django.core.files import File
from datetime import timedelta
from myapp.models import DonationEvent


class Donation(models.Model):
    DONATION_METHODS = [
        ('Bank Transfer', 'Bank Transfer'),
        ('Online Payment', 'Online Payment'),
    ]
    
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    donation_method = models.CharField(max_length=20, choices=DONATION_METHODS)
    date = models.DateTimeField(auto_now_add=True)
    message = models.TextField(blank=True, null=True)
    def __str__(self):
        return f"Donation from {self.name} - {self.amount} {self.donation_method}"

class Donor(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
class Transaction(models.Model):
    donation = models.ForeignKey(Donation, related_name='transactions', on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=255, unique=True)
    transaction_date = models.DateTimeField(auto_now_add=True)
    status_choices = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=status_choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"Transaction {self.transaction_id} for {self.amount}"



class Payment(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    donor = models.ForeignKey('Donor', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=[('Completed', 'Completed'), ('Pending', 'Pending')])
    payment_method = models.CharField(max_length=100)
    transaction_id = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"Payment of {self.amount} from {self.donor.name} on {self.date}"

def default_end_date():
    return timezone.now().date() + timedelta(days=30)

class DonationCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

# Removed DonationEvent model to avoid conflicts with myapp.DonationEvent

class DonorEngagementMessage(models.Model):
    MESSAGE_TYPES = [
        ('thank_you', 'Thank You Message'),
        ('impact_report', 'Impact Report'),
        ('reengagement', 'Re-engagement Suggestion'),
        ('anniversary', 'Anniversary Message'),
    ]
    
    donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='engagement_messages')
    event = models.ForeignKey(DonationEvent, on_delete=models.CASCADE, related_name='engagement_messages')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES)
    message_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.get_message_type_display()} for {self.donor.username} - {self.event.title}"

class DonationCart(models.Model):
    """Cart for storing donation events that users want to donate to"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='donation_carts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Cart for {self.user.username} - {self.created_at.strftime('%Y-%m-%d')}"
    
    def get_total_items(self):
        """Get total number of items in cart"""
        return self.cart_items.count()
    
    def get_total_amount(self):
        """Get total amount of all items in cart"""
        return sum(item.amount for item in self.cart_items.all())
    
    def clear_cart(self):
        """Remove all items from cart"""
        self.cart_items.all().delete()

class DonationCartItem(models.Model):
    """Individual items in the donation cart"""
    cart = models.ForeignKey(DonationCart, on_delete=models.CASCADE, related_name='cart_items')
    event = models.ForeignKey(DonationEvent, on_delete=models.CASCADE, related_name='cart_items')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    message = models.TextField(blank=True, null=True, max_length=200)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-added_at']
        unique_together = ['cart', 'event']  # Prevent duplicate events in cart
    
    def __str__(self):
        return f"{self.event.title} - ${self.amount} in {self.cart.user.username}'s cart"
    
    def get_progress_percentage(self):
        """Get progress percentage for this event"""
        if self.event.target_amount > 0:
            return min(100, round((self.event.current_amount / self.event.target_amount) * 100, 2))
        return 0