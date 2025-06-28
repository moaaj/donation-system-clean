from django.db import models
from django.utils import timezone

class WaqafAsset(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    current_value = models.DecimalField(max_digits=10, decimal_places=2)
    total_slots = models.PositiveIntegerField(default=0)
    slots_available = models.PositiveIntegerField(default=0)
    slot_price = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)  # Default RM50 per slot

    def __str__(self):
        return self.name

    def update_slots(self):
        self.slots_available = self.total_slots - self.contribution_set.count()
        self.save()

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

class FundDistribution(models.Model):
    asset = models.ForeignKey(WaqafAsset, on_delete=models.CASCADE)
    contributor = models.ForeignKey(Contributor, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    purpose = models.CharField(max_length=255)
    date_distributed = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.asset.name} - {self.amount} RM for {self.purpose}"
