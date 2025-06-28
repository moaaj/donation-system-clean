from django.db import models

# ------------------- Donor -------------------
class Donor(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

# ------------------- Donation -------------------
class Donation(models.Model):
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    message = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Donation by {self.donor.name} - {self.amount}"

# ------------------- Constants -------------------
PAYMENT_METHODS = [
    ('sslcommerz', 'SSLCommerz'),
    ('stripe', 'Stripe'),
    ('paypal', 'PayPal'),
    ('bank', 'Bank Transfer'),
    ('bkash', 'bKash'),
    ('nagad', 'Nagad'),
    ('cash', 'Cash'),
]

# ------------------- Transaction -------------------
class Transaction(models.Model):
    donation = models.ForeignKey(Donation, on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=255, unique=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=50, choices=[
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], default='pending')
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.status}"
