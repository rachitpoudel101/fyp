from django.shortcuts import redirect, render

# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from .models import Order, Product, Category
from user.models import CustomUser

@login_required
def dashboard(request):
    if not request.user.is_email_verified:
        return redirect('verify_pending')
        
    # Get date ranges
    today = timezone.now()
    thirty_days_ago = today - timedelta(days=30)
    
    # Calculate metrics
    total_sales = Order.objects.filter(
        created_at__gte=thirty_days_ago
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    total_orders = Order.objects.filter(
        created_at__gte=thirty_days_ago
    ).count()
    
    total_customers = CustomUser.objects.filter(
        order__created_at__gte=thirty_days_ago
    ).distinct().count()
    
    # Calculate changes from previous period
    previous_period = Order.objects.filter(
        created_at__gte=thirty_days_ago - timedelta(days=30),
        created_at__lt=thirty_days_ago
    )
    
    previous_sales = previous_period.aggregate(
        Sum('total_amount')
    )['total_amount__sum'] or 0
    
    sales_change = ((total_sales - previous_sales) / previous_sales * 100) if previous_sales else 0
    
    # Get recent orders
    recent_orders = Order.objects.select_related('customer').order_by('-created_at')[:5]
    
    # Get top selling products
    top_products = Product.objects.annotate(
        total_sales=Count('orderitem')
    ).order_by('-total_sales')[:5]
    
    context = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'sales_change': sales_change,
        'recent_orders': recent_orders,
        'top_products': top_products,
    }
    
    if request.user.role == 'admin':
        return render(request, 'admin_dashboard.html', context)
    else:
        return render(request, 'warehouse_dashboard.html', context)