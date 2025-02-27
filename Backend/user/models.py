from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.crypto import get_random_string

class Warehouse(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    manager = models.OneToOneField('CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_warehouse')

    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('warehouse_manager', 'Warehouse Manager'),
        ('customer', 'Customer'),
    ]
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    email = models.EmailField(unique=True, blank=False, null=False)
    is_email_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=64, blank=True, null=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')

    def generate_verification_token(self):
        """Generate a new unique verification token."""
        self.verification_token = get_random_string(length=32)
        self.save()