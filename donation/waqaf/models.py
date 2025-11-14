from django.db import models
from django.utils import timezone
from datetime import timedelta
import uuid

class WaqafAsset(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    current_value = models.DecimalField(max_digits=10, decimal_places=2)
    target_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Total amount needed for this asset')
    total_slots = models.PositiveIntegerField(default=0)
    slots_available = models.PositiveIntegerField(default=0)
    slot_price = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)  # Auto-calculated based on target_amount/total_slots
    is_archived = models.BooleanField(default=False, help_text='Archive this asset to hide it from public view')
    archived_at = models.DateTimeField(blank=True, null=True, help_text='When this asset was archived')
    archived_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, help_text='User who archived this asset')

    def __str__(self):
        return self.name

    def calculate_slot_price(self):
        """Calculate slot price based on target amount and total slots"""
        if self.target_amount > 0 and self.total_slots > 0:
            return self.target_amount / self.total_slots
        return self.slot_price  # Return current slot_price if calculation not possible

    def update_slot_price(self):
        """Update slot price based on target amount and total slots"""
        if self.target_amount > 0 and self.total_slots > 0:
            self.slot_price = self.target_amount / self.total_slots
            self.save(update_fields=['slot_price'])

    def update_slots(self):
        self.slots_available = self.total_slots - self.contribution_set.count()
        self.save()

    def save(self, *args, **kwargs):
        # Auto-calculate slot price if target_amount and total_slots are set
        if self.target_amount > 0 and self.total_slots > 0:
            self.slot_price = self.target_amount / self.total_slots
        super().save(*args, **kwargs)

    def archive(self, user=None):
        """Archive this asset"""
        self.is_archived = True
        self.archived_at = timezone.now()
        self.archived_by = user
        self.save()

    def unarchive(self):
        """Unarchive this asset"""
        self.is_archived = False
        self.archived_at = None
        self.archived_by = None
        self.save()

    def is_fully_funded(self):
        """Check if asset is fully funded"""
        return self.contribution_set.count() >= self.total_slots

    def get_funding_progress(self):
        """Get funding progress percentage"""
        if self.total_slots == 0:
            return 0
        filled_slots = self.total_slots - self.slots_available
        return (filled_slots / self.total_slots) * 100

    def get_status_display(self):
        """Get human-readable status"""
        if self.is_archived:
            return "Archived"
        elif self.slots_available == 0:
            return "Completed"
        elif self.slots_available < self.total_slots:
            return "In Progress"
        else:
            return "Available"

    def get_contribution_count(self):
        """Get total number of contributions for this asset"""
        return self.contribution_set.count()

    def get_total_contributed(self):
        """Get total amount contributed for this asset"""
        return self.contribution_set.aggregate(
            total=models.Sum('amount')
        )['total'] or 0

    class Meta:
        verbose_name = "Waqaf Asset"
        verbose_name_plural = "Waqaf Assets"
        ordering = ['name']

class Contributor(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    amount_contributed = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.name

    def update_total_contribution(self):
        total = sum(contribution.amount for contribution in self.contribution_set.all())
        self.amount_contributed = total
        self.save()

class Contribution(models.Model):
    contributor = models.ForeignKey(Contributor, on_delete=models.CASCADE)
    asset = models.ForeignKey(WaqafAsset, on_delete=models.CASCADE, null=True, blank=True)  # Made nullable for migration
    number_of_slots = models.PositiveIntegerField(default=1)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_contributed = models.DateTimeField(default=timezone.now)
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('COMPLETED', 'Completed'),
            ('FAILED', 'Failed')
        ],
        default='PENDING'
    )
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    dedicated_for = models.CharField(max_length=255, blank=True, null=True, help_text='E.g. For late mother, father, etc.')
    PAYMENT_TYPE_CHOICES = [
        ('ONE_OFF', 'One-off'),
        ('RECURRING', 'Recurring (Bank Auto-Deduction)')
    ]
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='ONE_OFF')
    
    # Payment scheduling fields
    payment_schedule = models.CharField(
        max_length=20,
        choices=[
            ('IMMEDIATE', 'Immediate'),
            ('WEEKLY', 'Weekly'),
            ('MONTHLY', 'Monthly'),
            ('QUARTERLY', 'Quarterly'),
            ('YEARLY', 'Yearly')
        ],
        default='IMMEDIATE'
    )
    next_payment_date = models.DateTimeField(blank=True, null=True)
    total_payments = models.PositiveIntegerField(default=1)
    payments_made = models.PositiveIntegerField(default=0)
    auto_generate_payments = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.contributor.name} - {self.number_of_slots} slots ({self.amount} RM)"

    def save(self, *args, **kwargs):
        if self.asset:  # Only calculate amount if asset is set
            self.amount = self.number_of_slots * self.asset.slot_price
        super().save(*args, **kwargs)
        # Update contributor's total contribution
        self.contributor.update_total_contribution()
        # Update asset's available slots if asset exists
        if self.asset:
            self.asset.update_slots()
        
        # Auto-generate payments if enabled
        if self.auto_generate_payments and self.payment_type == 'RECURRING':
            self.generate_payment_schedule()

    def generate_payment_schedule(self):
        """Generate payment schedule for recurring contributions"""
        if self.payment_type != 'RECURRING':
            return
        
        # Calculate payment amount per installment
        payment_amount = self.amount / self.total_payments
        
        # Set next payment date based on schedule
        if self.payment_schedule == 'WEEKLY':
            interval = timedelta(weeks=1)
        elif self.payment_schedule == 'MONTHLY':
            interval = timedelta(days=30)
        elif self.payment_schedule == 'QUARTERLY':
            interval = timedelta(days=90)
        elif self.payment_schedule == 'YEARLY':
            interval = timedelta(days=365)
        else:
            interval = timedelta(days=0)  # Immediate
        
        # Create payments
        for i in range(self.total_payments):
            payment_date = self.date_contributed + (interval * i)
            
            # Create payment record
            Payment.objects.create(
                contribution=self,
                amount=payment_amount,
                due_date=payment_date,
                payment_number=i + 1,
                status='PENDING' if i > 0 else 'COMPLETED'  # First payment is completed
            )
        
        # Set next payment date
        if self.total_payments > 1:
            self.next_payment_date = self.date_contributed + interval
            self.save(update_fields=['next_payment_date'])

    def get_payment_progress(self):
        """Get payment progress percentage"""
        if self.total_payments == 0:
            return 0
        return (self.payments_made / self.total_payments) * 100

class Payment(models.Model):
    """Model for individual payments within a contribution"""
    contribution = models.ForeignKey(Contribution, on_delete=models.CASCADE, related_name='payments')
    payment_id = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateTimeField()
    payment_date = models.DateTimeField(blank=True, null=True)
    payment_number = models.PositiveIntegerField()  # 1, 2, 3, etc.
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    PAYMENT_METHOD_CHOICES = [
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CHEQUE', 'Cheque'),
        ('ONLINE', 'Online Payment'),
        ('AUTO_DEDUCTION', 'Auto Deduction')
    ]
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)
    
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date', 'payment_number']
        unique_together = ['contribution', 'payment_number']

    def __str__(self):
        return f"Payment {self.payment_number} - {self.contribution.contributor.name} - RM{self.amount}"

    def save(self, *args, **kwargs):
        # Auto-generate payment ID if not set
        if not self.payment_id:
            self.payment_id = str(uuid.uuid4())
        
        # Update status based on due date
        if self.status == 'PENDING' and self.due_date < timezone.now():
            self.status = 'OVERDUE'
        
        super().save(*args, **kwargs)
        
        # Update contribution payment status
        self.update_contribution_status()

    def update_contribution_status(self):
        """Update the parent contribution's payment status"""
        contribution = self.contribution
        
        # Count completed payments
        completed_payments = contribution.payments.filter(status='COMPLETED').count()
        contribution.payments_made = completed_payments
        
        # Update contribution status
        if completed_payments == contribution.total_payments:
            contribution.payment_status = 'COMPLETED'
        elif completed_payments > 0:
            contribution.payment_status = 'PENDING'
        else:
            contribution.payment_status = 'PENDING'
        
        contribution.save(update_fields=['payments_made', 'payment_status'])

    def mark_as_paid(self, payment_method=None, reference_number=None, notes=None):
        """Mark payment as completed"""
        self.status = 'COMPLETED'
        self.payment_date = timezone.now()
        if payment_method:
            self.payment_method = payment_method
        if reference_number:
            self.reference_number = reference_number
        if notes:
            self.notes = notes
        self.save()

    def is_overdue(self):
        """Check if payment is overdue"""
        return self.status == 'PENDING' and self.due_date < timezone.now()

    def get_days_overdue(self):
        """Get number of days overdue"""
        if self.is_overdue():
            return (timezone.now() - self.due_date).days
        return 0

class FundDistribution(models.Model):
    asset = models.ForeignKey(WaqafAsset, on_delete=models.CASCADE)
    contributor = models.ForeignKey(Contributor, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    purpose = models.CharField(max_length=255)
    date_distributed = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.asset.name} - {self.amount} RM for {self.purpose}"

class WaqafCart(models.Model):
    """Cart for waqaf assets"""
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Cart for {self.user.username}"
    
    @property
    def total_amount(self):
        return sum(item.total_amount for item in self.items.all())
    
    @property
    def total_slots(self):
        return sum(item.number_of_slots for item in self.items.all())
    
    def clear(self):
        self.items.all().delete()

class WaqafCartItem(models.Model):
    """Individual items in waqaf cart"""
    cart = models.ForeignKey(WaqafCart, on_delete=models.CASCADE, related_name='items')
    asset = models.ForeignKey(WaqafAsset, on_delete=models.CASCADE)
    number_of_slots = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.asset.name} - {self.number_of_slots} slots"
    
    @property
    def total_amount(self):
        return self.number_of_slots * self.asset.slot_price
    
    @property
    def slot_price(self):
        return self.asset.slot_price
