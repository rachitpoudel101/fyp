from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order, OrderItem
from user.models import Notification, CustomUser

@receiver(post_save, sender=Order)
def notify_warehouse_managers(sender, instance, created, **kwargs):
    """
    When an order is created, notify all warehouse managers that have products in this order
    """
    if created:
        # Get the order items
        order_items = OrderItem.objects.filter(order=instance)
        
        # Find unique warehouses involved in this order
        warehouses_involved = set()
        for item in order_items:
            if item.product and item.product.warehouse:
                warehouses_involved.add(item.product.warehouse)
        
        # For each warehouse, notify its manager
        for warehouse in warehouses_involved:
            if warehouse.manager:
                # Create a notification for the warehouse manager
                Notification.objects.create(
                    user=warehouse.manager,
                    notification_type='order',
                    title=f"New Order #{instance.order_number}",
                    message=f"A new order containing products from your warehouse has been placed.",
                    related_order=instance
                )

@receiver(post_save, sender=Order)
def notify_on_status_change(sender, instance, created, **kwargs):
    """
    When an order status changes, notify relevant warehouse managers
    """
    if not created:  # Only proceed if this is an update, not a new creation
        # Get the order items
        order_items = OrderItem.objects.filter(order=instance)
        
        # Find unique warehouses involved in this order
        warehouses_involved = set()
        for item in order_items:
            if item.product and item.product.warehouse:
                warehouses_involved.add(item.product.warehouse)
        
        # For each warehouse, notify its manager about the status change
        for warehouse in warehouses_involved:
            if warehouse.manager:
                # Create a notification for the warehouse manager
                Notification.objects.create(
                    user=warehouse.manager,
                    notification_type='status',
                    title=f"Order #{instance.order_number} Status Update",
                    message=f"Order status has been updated to: {instance.status}",
                    related_order=instance
                )
