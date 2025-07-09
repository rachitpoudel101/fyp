from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.crypto import get_random_string


class Warehouse(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    manager = models.OneToOneField(
        "CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_warehouse",
    )
    handles_expiring = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({'Expiring' if self.handles_expiring else 'Non-Expiring'} Products)"


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ("super_admin", "Super Admin"),
        ("admin", "Admin"),
        ("warehouse_manager", "Warehouse Manager"),
        ("staff", "Staff"),
        ("customer", "Customer"),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="customer")
    email = models.EmailField(unique=True, blank=False, null=False)
    is_email_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, blank=True, null=True)
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
    )
    is_approved = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_users",
    )
    reset_password_token = models.CharField(max_length=32, null=True, blank=True)
    reset_password_expires = models.DateTimeField(null=True, blank=True)

    def generate_verification_token(self):
        """Generate a new unique verification token."""
        self.verification_token = get_random_string(length=32)
        self.save()

    def save(self, *args, **kwargs):
        # Debug log to verify role before saving
        print(f"DEBUG: Saving user with username={self.username}, role={self.role}")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username

    @property
    def unread_notifications_count(self):
        return self.notifications.filter(is_read=False).count()


class ActivityLog(models.Model):
    admin = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="activities"
    )
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.admin.username} - {self.action} at {self.timestamp}"


class Cart(models.Model):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="cart"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

    @property
    def total_items(self):
        return self.items.count()

    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("Inventory.Product", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("cart", "product")

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in {self.cart}"

    @property
    def subtotal(self):
        """Calculate the subtotal for this cart item"""
        if (
            self.product
            and self.product.price is not None
            and self.quantity is not None
        ):
            return float(self.product.price * self.quantity)
        return 0.0


class Wishlist(models.Model):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="wishlist"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Wishlist for {self.user.username}"


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(
        Wishlist, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey("Inventory.Product", on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("wishlist", "product")

    def __str__(self):
        return f"{self.product.name} in {self.wishlist}"


class Notification(models.Model):
    """
    Model for storing notifications for users
    """

    NOTIFICATION_TYPES = (
        ("order", "New Order"),
        ("status", "Status Update"),
        ("stock", "Stock Alert"),
        ("general", "General Notification"),
    )

    user = models.ForeignKey(
        "CustomUser", on_delete=models.CASCADE, related_name="notifications"
    )
    notification_type = models.CharField(
        max_length=20, choices=NOTIFICATION_TYPES, default="general"
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    related_order = models.ForeignKey(
        "Inventory.Order", on_delete=models.CASCADE, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    def mark_as_read(self):
        self.is_read = True
        self.save()
