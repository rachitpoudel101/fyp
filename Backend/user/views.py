from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.contrib.auth.decorators import login_required
from Inventory.models import Order, OrderItem, Product, Category
from Inventory.forms import CategoryForm, ProductForm, OrderForm
from .forms import CustomUserCreationForm, WarehouseForm
from .models import CustomUser, Warehouse
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.urls import reverse
import uuid
from django.db.models import Sum
from django.contrib import messages  # Import for user notifications

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

            # Generate verification link
            verification_link = request.build_absolute_uri(
                reverse('verify_email', args=[user.verification_token])
            )

            # Send verification email
            send_mail(
                'Verify your email',
                f'Click the link to verify your email: {verification_link}',
                'your_email@example.com',  # ✅ Add from_email (replace with your email)
                [user.email],  # ✅ Ensure recipient_list is a list
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
        elif 'assign_manager' in request.POST:
            warehouse_id = request.POST.get('warehouse_id')
            manager_id = request.POST.get('manager_id')
            warehouse = get_object_or_404(Warehouse, id=warehouse_id)
            manager = get_object_or_404(CustomUser, id=manager_id)
            warehouse.manager = manager
            warehouse.save()
            return JsonResponse({'success': True})
        else:
            form = ProductForm(request.POST)
            if form.is_valid():
                product = form.save(commit=False)
                if product.expires:
                    warehouse = Warehouse.objects.get(name="Expires Warehouse")
                else:
                    warehouse = Warehouse.objects.get(name="Non-Expires Warehouse")
                product.warehouse = warehouse
                product.save()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': form.errors.as_json()})
    
    total_sales = Order.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_orders = Order.objects.count()
    total_customers = CustomUser.objects.filter(role='customer').count()
    recent_orders = Order.objects.order_by('-created_at')[:5]
    products = Product.objects.all()
    users = CustomUser.objects.all()
    warehouses = Warehouse.objects.all()
    
    # Low stock threshold
    low_stock_threshold = 10
    low_stock_products = Product.objects.filter(stock__lt=low_stock_threshold)
    
    context = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'recent_orders': recent_orders,
        'products': products,
        'form': ProductForm(),
        'users': users,
        'warehouses': warehouses,
        'low_stock_products': low_stock_products,
        'user_form': CustomUserCreationForm(),  # Add user creation form
    }
    return render(request, 'admin_dashboard.html', context)

@login_required
def create_warehouse(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden("You are not authorized to view this page")
    
    if request.method == "POST":
        form = WarehouseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    else:
        form = WarehouseForm()
    
    return render(request, 'create_warehouse.html', {'form': form})

@login_required
def manage_warehouses(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden("You are not authorized to view this page")
    
    warehouses = Warehouse.objects.all()
    return render(request, 'manage_warehouses.html', {'warehouses': warehouses})

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
    
    context = {'users': users}
    return render(request, 'user_statistics.html', context)

@login_required
def product_management(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden("You are not authorized to view this page")
    
    if request.method == "POST":
        if 'delete_product_id' in request.POST:
            product_id = request.POST.get('delete_product_id')
            product = get_object_or_404(Product, id=product_id)
            product.delete()
            return JsonResponse({'success': True})
        
        product_id = request.POST.get('product_id')
        if product_id:
            # Edit existing product
            product = get_object_or_404(Product, id=product_id)
            form = ProductForm(request.POST, instance=product)
        else:
            # Create new product
            form = ProductForm(request.POST)
        
        if form.is_valid():
            product = form.save(commit=False)
            # Assign warehouse based on expiry date
            if product.expires:
                warehouse = Warehouse.objects.get_or_create(
                    name="Expires Warehouse",
                    defaults={'location': 'Default Location'}
                )[0]
            else:
                warehouse = Warehouse.objects.get_or_create(
                    name="Non-Expires Warehouse",
                    defaults={'location': 'Default Location'}
                )[0]
            product.warehouse = warehouse
            product.save()
            return JsonResponse({'success': True})
        else:
            # Return detailed form errors
            return JsonResponse({'success': False, 'error': form.errors.as_json()})

    products = Product.objects.all()
    categories = Category.objects.all()
    warehouses = Warehouse.objects.all()
    
    context = {
        'products': products,
        'categories': categories,
        'warehouses': warehouses,
        'form': ProductForm()  # Ensure the form is passed to the template
    }
    return render(request, 'product_management.html', context)

@login_required
def update_product(request, product_id):
    if request.user.role != 'admin':
        return HttpResponseForbidden("You are not authorized to perform this action")
    
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save(commit=False)
            if product.expires:
                warehouse = Warehouse.objects.get_or_create(
                    name="Expires Warehouse",
                    defaults={'location': 'Default Location'}
                )[0]
            else:
                warehouse = Warehouse.objects.get_or_create(
                    name="Non-Expires Warehouse",
                    defaults={'location': 'Default Location'}
                )[0]
            product.warehouse = warehouse
            product.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'error': form.errors})
    
    data = {
        'id': product.id,
        'name': product.name,
        'category': product.category.id if product.category else None,
        'price': str(product.price),
        'stock': product.stock,
        'description': product.description,
        'expires': product.expires.isoformat() if product.expires else None,
    }
    return JsonResponse(data)

@login_required
def add_category(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden("You are not authorized to perform this action")
    
    if request.method == "POST":
        name = request.POST.get('category_name')
        description = request.POST.get('category_description')
        
        try:
            category = Category.objects.create(
                name=name,
                description=description
            )
            return JsonResponse({
                'success': True, 
                'id': category.id,
                'name': category.name
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return HttpResponseBadRequest()

@login_required
def billing(request):
    orders = Order.objects.filter(customer=request.user)
    return render(request, 'billing.html', {'orders': orders})

@login_required
def get_product_details(request, product_id):
    if request.user.role != 'admin':
        return HttpResponseForbidden("You are not authorized to perform this action")
    
    product = get_object_or_404(Product, id=product_id)
    data = {
        'category': product.category.id,
        'description': product.description,
    }
    return JsonResponse(data)

@login_required
def resend_verification_email(request):
    if not request.user.is_email_verified:
        user = request.user
        user.generate_verification_token()  # Generate a new token
        user.save()

        # Generate verification link
        verification_link = request.build_absolute_uri(
            reverse('verify_email', args=[user.verification_token])
        )

        # Send verification email
        send_mail(
            'Verify your email',
            f'Click the link to verify your email: {verification_link}',
            'your_email@example.com',  # Replace with your email
            [user.email],
        )

        messages.success(request, "Verification email has been resent.")
    else:
        messages.info(request, "Your email is already verified.")

    return redirect('verify_pending')

@login_required
def add_user(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden("You are not authorized to perform this action")
    
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.set_password(form.cleaned_data['password1'])
                user.is_email_verified = False  # Mark email as not verified
                user.generate_verification_token()  # Generate token
                user.role = request.POST.get('role')  # Save the role
                user.save()

                # Optionally send a verification email
                verification_link = request.build_absolute_uri(
                    reverse('verify_email', args=[user.verification_token])
                )
                send_mail(
                    'Verify your email',
                    f'Click the link to verify your email: {verification_link}',
                    'your_email@example.com',  # Replace with your email
                    [user.email],
                )
                messages.success(request, "User has been successfully created.")
                return JsonResponse({'success': True})
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
                return JsonResponse({'success': False, 'error': str(e)})
        else:
            errors = form.errors.as_json()
            messages.error(request, "Failed to create user. Please check the form.")
            return JsonResponse({'success': False, 'error': errors})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})