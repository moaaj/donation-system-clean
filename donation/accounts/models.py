from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """Extended user profile for additional information"""
    ROLE_CHOICES = [
        ('superuser', 'Superuser'),
        ('admin', 'Admin'),
        ('waqaf_admin', 'Waqaf Admin'),
        ('donation_admin', 'Donation Admin'),
        ('form1_admin', 'Form 1 Admin'),
        ('form3_admin', 'Form 3 Admin'),
        ('student', 'Student'),
        ('regular', 'Regular User'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='regular')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.username}'s Profile ({self.role})"
    
    def is_waqaf_admin(self):
        """Check if user is a waqaf admin"""
        return self.role == 'waqaf_admin'
    
    def is_donation_admin(self):
        """Check if user is a donation admin"""
        return self.role == 'donation_admin'
    
    def is_form1_admin(self):
        """Check if user is a Form 1 admin"""
        return self.role == 'form1_admin'
    
    def is_form3_admin(self):
        """Check if user is a Form 3 admin"""
        return self.role == 'form3_admin'
    
    def is_superuser(self):
        """Check if user is a superuser"""
        return self.role == 'superuser' or self.user.is_superuser
    
    def is_admin(self):
        """Check if user is an admin"""
        return self.role in ['admin', 'superuser'] or self.user.is_staff


class LoginAttempt(models.Model):
    """Track login attempts for security"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Login Attempt'
        verbose_name_plural = 'Login Attempts'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username if self.user else 'Unknown'} - {self.ip_address} - {'Success' if self.success else 'Failed'}"


class UserActivity(models.Model):
    """Track user login/logout activity for superuser monitoring"""
    ACTIVITY_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=10, choices=ACTIVITY_TYPES)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'User Activity'
        verbose_name_plural = 'User Activities'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create user profile when user is created"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save user profile when user is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save() 