from django import forms
from .models import Product, Category, Order, OrderItem

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'price', 'stock', 'description']

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['order_number', 'total_amount', 'status']

class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['order', 'product', 'quantity', 'price']