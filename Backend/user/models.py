from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.crypto import get_random_string

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('warehouse_manager', 'Warehouse Manager'),
        ('customer', 'customer'),
    ]
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    email = models.EmailField(unique=True, blank=False, null=False)
    is_email_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=64, blank=True, null=True)
    verification_token = models.CharField(max_length=64, null=True, blank=True)

    def generate_verification_token(self):
        """Generate a new unique verification token."""
        self.verification_token = get_random_string(length=32)
        self.save()