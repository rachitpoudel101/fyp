from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib.auth.decorators import login_required
from inventory.models import Order, OrderItem, Product, Category
from inventory.forms import ProductForm, OrderForm
from .forms import CustomUserCreationForm
from .models import CustomUser
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.urls import reverse
import uuid
from django.db.models import Sum

def verify_email(request, token):
    user = get_object_or_404(CustomUser, verification_token=token)
    user.is_email_verified = True
    user.verification_token = None  # Invalidate the token
    user.save()
    return render(request, 'email_verified.html')

def verify_pending(request):
    return render(request, 'verify_pending.html')

def generate_verification_token():
    return get_random_string(length=32)

# Sign up view - Allows users to register with a role
def signup(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.is_email_verified = False  # Mark email as not verified
            user.generate_verification_token()  # Generate token
            user.save()

            # Send verification email
            verification_link = request.build_absolute_uri(
                reverse('verify_email', args=[user.verification_token])
            )
            send_mail(
                'Verify your email',
                f'Click the link to verify your email: {verification_link}',
                [user.email],
            )
            return redirect('verify_pending')  # Redirect to a pending page
    else:
        form = CustomUserCreationForm()
    return render(request, 'signup.html', {'form': form})

def user_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)  # Log the user in
            if user.role == 'admin':
                return redirect('admin_dashboard')
            elif user.role == 'warehouse_manager':
                return redirect('warehouse_dashboard')
            elif user.role == 'customer':
                return redirect('order_list')
            else:
                return HttpResponseForbidden("You do not have permission to view this page.")
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

# Logout view - Logs users out and redirects to login page
def user_logout(request):
    logout(request)
    return redirect('login')  # Redirect to login after logout

# Dashboard view - Redirects users to role-based dashboards
@login_required
def dashboard(request):
    if request.user.role == 'admin':
        return redirect('admin_dashboard')
    elif request.user.role == 'warehouse_manager':
        return redirect('warehouse_dashboard')
    elif request.user.role == 'customer':
        return redirect('order_list')
    else:
        return HttpResponseForbidden("You do not have permission to view this page.")

# Admin Dashboard - Only accessible by admin users
@login_required
def admin_dashboard(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden("You are not authorized to view this page")
    
    if request.method == "POST":
        if 'delete_product_id' in request.POST:
            product_id = request.POST.get('delete_product_id')
            product = get_object_or_404(Product, id=product_id)
            product.delete()
            return JsonResponse({'success': True})
        else:
            form = ProductForm(request.POST)
            if form.is_valid():
                form.save()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': form.errors.as_json()})
    
    total_sales = Order.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_orders = Order.objects.count()
    total_customers = CustomUser.objects.filter(role='customer').count()
    recent_orders = Order.objects.order_by('-created_at')[:5]
    products = Product.objects.all()
    users = CustomUser.objects.all()
    
    context = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'recent_orders': recent_orders,
        'products': products,
        'form': ProductForm(),
        'users': users,
    }
    return render(request, 'admin_dashboard.html', context)

# Warehouse Manager Dashboard - Only accessible by warehouse manager users
@login_required
def warehouse_dashboard(request):
    if request.user.role != 'warehouse_manager':
        return HttpResponseForbidden("You are not authorized to view this page")
    return render(request, 'warehouse_dashboard.html')

@login_required
def inventory(request):
    if request.user.role != 'warehouse_manager':
        return HttpResponseForbidden("You are not authorized to view this page")
    
    if request.method == "POST":
        product_id = request.POST.get('product_id')
        stock_change = int(request.POST.get('stock_change'))
        product = get_object_or_404(Product, id=product_id)
        product.stock += stock_change
        product.save()
        return redirect('inventory')
    
    products = Product.objects.all()
    return render(request, 'inventory.html', {'products': products})

@login_required
def orders(request):
    if request.user.role != 'warehouse_manager':
        return HttpResponseForbidden("You are not authorized to view this page")
    
    recent_orders = Order.objects.filter(status='pending')
    canceled_orders = Order.objects.filter(status='cancelled')
    return render(request, 'orders.html', {'recent_orders': recent_orders, 'canceled_orders': canceled_orders})

@login_required
def update_order_status(request, order_id):
    if request.user.role != 'warehouse_manager':
        return HttpResponseForbidden("You are not authorized to view this page")
    
    order = get_object_or_404(Order, id=order_id)
    if request.method == "POST":
        status = request.POST.get('status')
        order.status = status
        order.save()
        return redirect('orders')
    return render(request, 'orders.html')

# Customer views
@login_required
def create_order(request):
    if request.user.role != 'customer':
        return HttpResponseForbidden("You are not authorized to view this page")
    
    if request.method == "POST":
        product_id = request.POST.get('product')
        quantity = int(request.POST.get('quantity'))
        product = get_object_or_404(Product, id=product_id)
        
        if product.stock < quantity:
            return HttpResponseForbidden("Not enough stock available")
        
        order = Order.objects.create(
            order_number=str(uuid.uuid4()),
            customer=request.user,
            total_amount=product.price * quantity,
            status='pending'
        )
        
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price=product.price
        )
        
        # Decrease stock
        product.stock -= quantity
        product.save()
        
        return redirect('order_detail', order_id=order.id)
    
    products = Product.objects.all()
    return render(request, 'create_order.html', {'products': products})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.user.role != 'customer' or order.customer != request.user:
        return HttpResponseForbidden("You are not authorized to view this page")
    return render(request, 'order_detail.html', {'order': order})

@login_required
def order_list(request):
    if request.user.role == 'customer':
        orders = Order.objects.filter(customer=request.user)
        products = Product.objects.all()
        return render(request, 'order_list.html', {'orders': orders, 'products': products})
    elif request.user.role == 'warehouse_manager':
        orders = Order.objects.all()
        return render(request, 'order_list.html', {'orders': orders})
    else:
        return HttpResponseForbidden("You are not authorized to view this page")

@login_required
def user_statistics(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden("You are not authorized to view this page")
    
    users = CustomUser.objects.all()
    
    context = {'users': users
    }
    return render(request, 'user_statistics.html', context)

def product_management(request):
    products = Product.objects.all()
    return render(request, 'product_management.html', {'products': products})