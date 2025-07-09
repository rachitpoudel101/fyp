from django.contrib import admin
from .models import Profile, Category, Product, Order, OrderItem


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "address")
    search_fields = ("user__username", "user__email", "phone")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock", "created_at", "updated_at")
    list_filter = ("category", "created_at")
    search_fields = ("name", "description")
    readonly_fields = ("created_at", "updated_at")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "customer", "total_amount", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("order_number", "customer__username", "customer__email")
    readonly_fields = ("created_at", "updated_at")
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "quantity", "price")
    list_filter = ("order__status",)
    search_fields = ("order__order_number", "product__name")
