import json
from django.utils import timezone  #  timezone import
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.contrib.auth.decorators import login_required
from Inventory.models import Order, OrderItem, Product, Category
# from Inventory.forms import CategoryForm, ProductForm, OrderForm
from .forms import CustomUserCreationForm, WarehouseForm, StaffCreationForm
from .models import CustomUser, Warehouse, ActivityLog, Cart, CartItem, Wishlist, WishlistItem  
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.urls import reverse
import uuid
from django.db.models import Sum, Q, F
from django.contrib import messages  # Import for user notifications
from django.views.decorators.http import require_POST, require_http_methods
from django.db import transaction  # Add this import
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

def verify_email(request, token):
    try:
        # Debug log to see what token we're looking for
        print(f"DEBUG: Attempting to verify email with token: {token}")
        
        # Try to find the user with this token
        user = CustomUser.objects.filter(verification_token=token).first()
        
        if not user:
            print(f"DEBUG: No user found with token: {token}")
            messages.error(request, "Invalid or expired verification link. Please request a new verification email.")
            return redirect('verify_pending')
            
        print(f"DEBUG: Found user: {user.username} with email: {user.email}")
        
        # Check if already verified
        if user.is_email_verified:
            print(f"DEBUG: User {user.username} is already verified")
            messages.info(request, "Your email is already verified. You can now log in.")
            return redirect('login')
            
        # Verify the user
        user.is_email_verified = True
        user.verification_token = None  # Invalidate the token
        user.save()
        
        print(f"DEBUG: Successfully verified user: {user.username}")
        messages.success(request, "Your email has been successfully verified!")
        
        return render(request, 'email_verified.html')
        
    except Exception as e:
        print(f"DEBUG: Error during email verification: {str(e)}")
        messages.error(request, "An error occurred during email verification. Please try again.")
        return redirect('verify_pending')

def verify_pending(request):
    return render(request, 'verify_pending.html')

def generate_verification_token():
    return get_random_string(length=32)

# Sign up view - Allows users to register with a role

def signup(request):
    if request.method == 'POST':
        # Create a mutable copy of POST data
        post_data = request.POST.copy()
        # Force role to be 'customer' for signup
        post_data['role'] = 'customer'
        
        form = CustomUserCreationForm(post_data)
        if form.is_valid():
            try:
                # Debug log to see form data
                print("DEBUG: Form data:", form.cleaned_data)
                
                user = form.save(commit=False)
                user.role = 'customer'  # Force role to be customer
                user.is_email_verified = False
                
                # Debug log before saving
                print("DEBUG: About to save user:", {
                    'username': user.username,
                    'email': user.email,
                    'role': user.role
                })
                
                user.save()
                
                # Debug log after saving
                print("DEBUG: User saved successfully with ID:", user.id)
                
                # Generate verification token
                token = generate_verification_token()
                user.verification_token = token
                user.save()
                
                # Send verification email
                verification_link = request.build_absolute_uri(
                    reverse('verify_email', args=[token])
                )
                send_mail(
                    'Verify your email',
                    f'Click the link to verify your email: {verification_link}',
                    'your_email@example.com',  # Replace with your email
                    [user.email],
                )
                
                messages.success(request, 'Account created successfully! Please check your email to verify your account.')
                
                # Log the successful creation
                print("DEBUG: Customer account created and verification email sent")
                
                return redirect('login')
                
            except Exception as e:
                # Log any errors that occur
                print("DEBUG: Error creating user:", str(e))
                messages.error(request, f'Error creating account: {str(e)}')
                return render(request, 'signup.html', {'form': form})
        else:
            # Log form validation errors
            print("DEBUG: Form validation errors:", form.errors)
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm(initial={'role': 'customer'})
    
    return render(request, 'signup.html', {'form': form})

def user_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Debug log to verify login credentials
        print(f"DEBUG: Attempting login with username={username}, password={password}")

        # Hardcoded super admin credentials
        if username == "superadmin" and password == "superadmin":
            # Simulate a super admin login
            user = CustomUser.objects.filter(role='super_admin').first()
            if not user:
                # Create a default super admin user
                user = CustomUser.objects.create_user(
                    username="superadmin",
                    email="superadmin@example.com",  # Replace with a valid email
                    password="superadmin",  # Default password
                    role="super_admin",
                    is_email_verified=True
                )
            login(request, user)
            return redirect('super_admin_dashboard')

        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            # Debug log to verify email verification status
            print(f"DEBUG: User email verification status: {user.is_email_verified}")
            if not user.is_email_verified:
                messages.error(request, "Your email is not verified. Please check your email for the verification link.")
                return redirect('login')
            login(request, user)  # Log the user in
            if user.role == 'super_admin':
                return redirect('super_admin_dashboard')
            elif user.role == 'admin':
                return redirect('admin_dashboard')
            elif user.role == 'warehouse_manager':
                return redirect('warehouse_dashboard')
            elif user.role == 'staff':
                return redirect('staff_dashboard')  # Add redirect for staff role
            elif user.role == 'customer':
                return redirect('order_list')
            else:
                return HttpResponseForbidden("You do not have permission to view this page.")
        else:
            # Debug log for invalid login
            print("DEBUG: Invalid login credentials")
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
    if request.user.role == 'super_admin':
        return redirect('super_admin_dashboard')
    if request.user.role == 'admin':
        return redirect('admin_dashboard')
    elif request.user.role == 'warehouse_manager':
        return redirect('warehouse_dashboard')
    elif request.user.role == 'staff':
        return redirect('staff_dashboard')  # Add this line
    elif request.user.role == 'customer':
        return redirect('customer_dashboard')  # Changed to redirect to customer dashboard
    else:
        return HttpResponseForbidden("You do not have permission to view this page.")

# Add the new customer dashboard view
@login_required
def customer_dashboard(request):
    if request.user.role != 'customer':
        return HttpResponseForbidden("You are not authorized to view this page")
    
    # Get customer's orders
    orders = Order.objects.filter(customer=request.user).order_by('-created_at')
    recent_orders = orders[:5]  # Get 5 most recent orders
    
    # Calculate statistics
    total_orders = orders.count()
    total_spent = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Get orders by status
    pending_orders = orders.filter(status='pending').count()
    delivered_orders = orders.filter(status='delivered').count()
    
    # Get some recommended products (just showing available products for now)
    recommended_products = Product.objects.filter(stock__gt=0)[:6]
    
    context = {
        'recent_orders': recent_orders,
        'total_orders': total_orders,
        'total_spent': total_spent,
        'pending_orders': pending_orders,
        'delivered_orders': delivered_orders,
        'recommended_products': recommended_products,
    }
    
    return render(request, 'customer_dashboard.html', context)

@login_required
def admin_dashboard(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden("You are not authorized to view this page")
    
    # Get warehouse managers and staff added by the current admin
    warehouse_managers = CustomUser.objects.filter(role='warehouse_manager', created_by=request.user)
    staff_members = CustomUser.objects.filter(role='staff', created_by=request.user)
    
    # Get all warehouses
    warehouses = Warehouse.objects.all()
    
    # Get available managers for warehouse assignment
    available_managers = CustomUser.objects.filter(
        role='warehouse_manager',
        managed_warehouse__isnull=True,
        is_active=True
    )
    
    # Get low stock products
    low_stock_products = Product.objects.filter(stock__lte=F('min_stock'))
    
    # Check for unread notifications - Add this block
    has_unread_notifications = False
    unread_notifications_count = 0
    try:
        if hasattr(request.user, 'notifications'):
            unread_notifications_count = request.user.notifications.filter(is_read=False).count()
            has_unread_notifications = unread_notifications_count > 0
    except Exception as e:
        print(f"Error checking notifications: {str(e)}")
    
    context = {
        'warehouse_managers': warehouse_managers,
        'staff_members': staff_members,
        'warehouses': warehouses,
        'available_managers': available_managers,
        'low_stock_products': low_stock_products,
        'user_form': CustomUserCreationForm(),
        'has_unread_notifications': has_unread_notifications,
        'unread_notifications_count': unread_notifications_count,
    }
    
    return render(request, 'admin_dashboard.html', context)

@login_required
def create_warehouse(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden("You are not authorized to perform this action")
    
    if request.method == 'POST':
        warehouse_name = request.POST.get('warehouse_name')
        location = request.POST.get('location')
        handles_expiring = request.POST.get('handles_expiring') == 'on'
        
        try:
            # Create new warehouse
            warehouse = Warehouse.objects.create(
                name=warehouse_name,
                location=location,
                handles_expiring=handles_expiring
            )
            # Log the activity
            ActivityLog.objects.create(
                admin=request.user,
                action=f"Created new warehouse: {warehouse_name}"
            )
            messages.success(request, f'Warehouse "{warehouse_name}" created successfully!')
            return redirect('admin_dashboard')
        except Exception as e:
            messages.error(request, f'Error creating warehouse: {str(e)}')
            return redirect('create_warehouse')
    
    return render(request, 'create_warehouse.html')

@login_required
def manage_warehouses(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden("You are not authorized to view this page")
    
    warehouses = Warehouse.objects.all()
    
    # Get ALL warehouse managers regardless of assignment status
    available_managers = CustomUser.objects.filter(
        role='warehouse_manager',
        is_active=True,
    )
    
    # Calculate statistics for the dashboard
    active_warehouses = warehouses.filter(manager__isnull=False)
    total_products = Product.objects.count()
    
    context = {
        'warehouses': warehouses,
        'available_managers': available_managers,
        'active_warehouses': active_warehouses,
        'total_products': total_products
    }
    
    return render(request, 'manage_warehouses.html', context)

# Warehouse Manager Dashboard - Only accessible by warehouse manager users
@login_required
def warehouse_dashboard(request):
    if request.user.role != 'warehouse_manager':
        return HttpResponseForbidden("You are not authorized to view this page")
    
    # Get the warehouse managed by this user
    warehouse = getattr(request.user, 'managed_warehouse', None)
    
    if not warehouse:
        messages.error(request, "You are not assigned to any warehouse yet")
        return render(request, 'warehouse_dashboard.html', {'no_warehouse': True})
    
    # Get recent orders that contain products from this warehouse
    from django.db.models import Count
    from Inventory.models import OrderItem, Order
    
    # Find order IDs that contain products from this warehouse
    order_ids = OrderItem.objects.filter(
        product__warehouse=warehouse
    ).values_list('order_id', flat=True).distinct()
    
    # Get those orders
    recent_orders = Order.objects.filter(
        id__in=order_ids
    ).order_by('-created_at')[:5]
    
    # Get staff members for assignment
    staff_members = CustomUser.objects.filter(role='staff', is_active=True)
    
    # Get count of orders by status
    pending_count = Order.objects.filter(id__in=order_ids, status='pending').count()
    processing_count = Order.objects.filter(id__in=order_ids, status='processing').count()
    shipped_count = Order.objects.filter(id__in=order_ids, status='shipped').count()
    delivered_count = Order.objects.filter(id__in=order_ids, status='delivered').count()
    
    # Get all warehouses
    warehouses = Warehouse.objects.all()
    
    # Get unread notifications if the table exists
    try:
        unread_notifications = request.user.notifications.filter(is_read=False)[:5]
        notification_count = unread_notifications.count()
    except Exception:
        # Handle the case when notifications aren't available
        unread_notifications = []
        notification_count = 0
    
    # Get low stock products
    low_stock_products = Product.objects.filter(stock__lte=F('min_stock'))
    
    context = {
        'warehouse': warehouse,
        'recent_orders': recent_orders,
        'pending_count': pending_count,
        'processing_count': processing_count,
        'shipped_count': shipped_count,
        'delivered_count': delivered_count,
        'total_orders': len(order_ids),
        'unread_notifications': unread_notifications,
        'notification_count': notification_count,
        'staff_members': staff_members,
        'warehouses': warehouses,
        'low_stock_products': low_stock_products,
        'user_form': CustomUserCreationForm()
    }
    
    return render(request, 'warehouse_dashboard.html', context)

@login_required
def warehouse_orders(request):
    """View for warehouse managers to see orders containing their warehouse's products"""
    if request.user.role != 'warehouse_manager':
        return HttpResponseForbidden("You are not authorized to view this page")
    
    # Get the warehouse managed by this user
    warehouse = getattr(request.user, 'managed_warehouse', None)
    
    if not warehouse:
        messages.error(request, "You are not assigned to any warehouse yet")
        return redirect('warehouse_dashboard')
    
    # Get status filter from query params
    status_filter = request.GET.get('status', '')
    
    # Find order IDs that contain products from this warehouse
    from Inventory.models import OrderItem, Order
    order_ids = OrderItem.objects.filter(
        product__warehouse=warehouse
    ).values_list('order_id', flat=True).distinct()
    
    # Get those orders
    orders = Order.objects.filter(id__in=order_ids)
    
    # Apply status filter if provided
    if status_filter and status_filter != 'all':
        orders = orders.filter(status=status_filter)
    
    # Order by most recent first
    orders = orders.order_by('-created_at')
    
    # Get available staff members for assignment
    staff_members = CustomUser.objects.filter(role='staff', is_active=True)
    
    context = {
        'warehouse': warehouse,
        'orders': orders,
        'current_status': status_filter or 'all',
        'staff_members': staff_members
    }
    
    return render(request, 'warehouse_orders.html', context)

@login_required
def view_notifications(request):
    """View for users to see all their notifications"""
    try:
        if request.method == 'POST':
            # Mark all as read if requested
            if 'mark_all_read' in request.POST:
                request.user.notifications.filter(is_read=False).update(is_read=True)
                messages.success(request, "All notifications marked as read")
                return redirect('view_notifications')
            
            # Mark specific notification as read
            notification_id = request.POST.get('notification_id')
            if notification_id:
                from .models import Notification
                notification = get_object_or_404(Notification, id=notification_id, user=request.user)
                notification.is_read = True
                notification.save()
                
                # If there's a related order, redirect to it
                if notification.related_order:
                    return redirect('order_detail', order_id=notification.related_order.id)
        
        # Get all notifications for this user
        notifications = request.user.notifications.all().order_by('-created_at')
        return render(request, 'notifications.html', {
            'notifications': notifications,
            'unread_count': notifications.filter(is_read=False).count()
        })
    except Exception:
        # If notifications aren't available, show an empty list
        messages.warning(request, "Notification system is not available at the moment.")
        return render(request, 'notifications.html', {
            'notifications': [],
            'unread_count': 0
        })

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
    
    # Get all orders with their status
    all_orders = Order.objects.all()
    
    context = {
        'recent_orders': all_orders.order_by('-created_at'),
        'total_orders': all_orders.count(),
        'pending_orders': all_orders.filter(status='pending').count(),
        'processing_orders': all_orders.filter(status='processing').count(),
        'completed_orders': all_orders.filter(status__in=['delivered', 'shipped']).count(),
        'delivered_orders': all_orders.filter(status='delivered').count(),
        'shipped_orders': all_orders.filter(status='shipped').count(),
        'cancelled_orders': all_orders.filter(status='cancelled').count(),
    }
    return render(request, 'orders.html', context)

@login_required
def update_order_status(request, order_id):
    if request.user.role != 'warehouse_manager':
        return HttpResponseForbidden("You are not authorized to perform this action")
    
    order = get_object_or_404(Order, id=order_id)
    if request.method == "POST":
        try:
            status = request.POST.get('status')
            old_status = order.status
            order.status = status
            order.save()
            
            # Log the status change
            ActivityLog.objects.create(
                admin=request.user,
                action=f"Updated order {order.order_number} status from {old_status} to {status}"
            )
            messages.success(request, f"Order status successfully updated to {status}")
        except Exception as e:
            messages.error(request, f"Error updating order status: {str(e)}")
        return redirect('orders')
    return redirect('orders')

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
        # Get or create cart and wishlist for displaying counts
        cart, _ = Cart.objects.get_or_create(user=request.user)
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        context = {
            'orders': orders,
            'products': products,
            'cart': cart,
            'wishlist': wishlist
        }
        return render(request, 'order_list.html', context)
    elif request.user.role == 'warehouse_manager':
        orders = Order.objects.all()
        return render(request, 'order_list.html', {'orders': orders})
    else:
        return HttpResponseForbidden("You are not authorized to view this page")

@login_required
def user_statistics(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden("You are not authorized to view this page")
    
    # Get all users with their creators (admins)
    users = CustomUser.objects.select_related('created_by').all().order_by('role')
    
    # Get users specifically created by the current admin
    users_created_by_me = CustomUser.objects.filter(created_by=request.user).select_related('created_by')
    
    # Get ALL warehouse managers and staff members regardless of created_by field
    # Added select_related('created_by') to efficiently load the creator information
    warehouse_managers = CustomUser.objects.filter(role='warehouse_manager').select_related('created_by')
    staff_members = CustomUser.objects.filter(role='staff').select_related('created_by')
    
    context = {
        'users': users,
        'users_created_by_me': users_created_by_me,
        'warehouse_managers': warehouse_managers,
        'staff_members': staff_members,
    }
    return render(request, 'user_statistics.html', context)


@login_required
def billing(request):
    orders = Order.objects.filter(customer=request.user)
    return render(request, 'billing.html', {'orders': orders})

@login_required
def get_product_details(request, product_id):
    """API endpoint to get product details for the edit form"""
    if request.user.role != 'admin':
        return HttpResponseForbidden("You are not authorized to perform this action")
    
    try:
        product = get_object_or_404(Product, id=product_id)
        data = {
            'id': product.id,
            'name': product.name,
            'category': product.category.id if product.category else None,
            'price': str(product.price),
            'stock': product.stock,
            'description': product.description,
            'expires': product.expires.isoformat() if product.expires else None,
            'warehouse': product.warehouse.id if product.warehouse else None,  # Add warehouse ID
        }
        return JsonResponse(data)
    except Exception as e:
        print(f"DEBUG: Error fetching product details: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

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
                user.is_email_verified = False
                user.generate_verification_token()
                user.role = request.POST.get('role')
                user.created_by = request.user  # Track who created the user
                user.save()
                
                # Send verification email
                verification_link = request.build_absolute_uri(
                    reverse('verify_email', args=[user.verification_token])
                )
                send_mail(
                    'Verify your email',
                    f'Click the link to verify your email: {verification_link}',
                    'your_email@example.com',
                    [user.email],
                )
                
                # Create notification for super admins
                from .models import Notification, CustomUser
                super_admins = CustomUser.objects.filter(role='super_admin')
                for admin in super_admins:
                    Notification.objects.create(
                        user=admin,
                        message=f"Admin {request.user.username} created a new {user.role}: {user.username}",
                        is_read=False
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

@login_required
def super_admin_dashboard(request):
    if request.user.role != 'super_admin':
        return HttpResponseForbidden("You are not authorized to view this page")
    
    # Get all admin categories
    admins = CustomUser.objects.filter(role='admin')
    verified_admins = admins.filter(is_verified=True)
    pending_admins = admins.filter(is_approved=False, is_verified=False)
    verification_requests = admins.filter(is_approved=True, is_verified=False)
    
    # Get recent activities
    recent_activities = ActivityLog.objects.order_by('-timestamp')[:10]
    
    context = {
        'admins': admins,
        'verified_admins': verified_admins,
        'pending_admins': pending_admins,
        'verification_requests': verification_requests,
        'recent_activities': recent_activities,
        'user_form': CustomUserCreationForm()
    }
    return render(request, 'super_admin_dashboard.html', context)

@login_required
def add_admin(request):
    if request.user.role != 'super_admin':
        return HttpResponseForbidden("You are not authorized to perform this action")
    
    if request.method == "POST":
        # Include request.FILES if your form handles file uploads
        form = CustomUserCreationForm(request.POST)
        # Important: Force role to be 'admin' before validation
        post_data = request.POST.copy()  # Create a mutable copy
        post_data['role'] = 'admin'  # Set role to admin
        form = CustomUserCreationForm(post_data)
        
        if form.is_valid():
            try:
                # Don't use commit=False since we want to test if it can save
                user = form.save(commit=False)
                raw_password = form.cleaned_data['password1']  # Get from cleaned_data
                user.role = 'admin'  # Ensure role is set to admin
                user.is_email_verified = False
                user.verification_token = get_random_string(length=32)
                user.created_by = request.user  # Set the creator to the current super admin
                
                # Debug with more details
                print(f"DEBUG: About to save admin - username={user.username}, email={user.email}, role={user.role}, created_by={user.created_by.username}")
                
                # Save the user
                user.save()
                print(f"DEBUG: Admin saved successfully with ID={user.id}")
                
                # Create activity log
                ActivityLog.objects.create(
                    admin=request.user,
                    action=f"Created new admin account for {user.username}"
                )
                
                # Generate verification link
                verification_link = request.build_absolute_uri(
                    reverse('verify_email', args=[user.verification_token])
                )
                
                # Send email with credentials and verification link
                send_mail(
                    'Admin Account Created',
                    f"""
                    Dear {user.username},
                    
                    Your admin account has been created. Please use the following credentials to log in after verifying your email:
                    
                    Username: {user.username}
                    Password: {raw_password}
                    
                    To verify your email, click the link below:
                    {verification_link}
                    
                    Thank you,
                    Super Admins
                    """,
                    'your_email@example.com',  # Replace with your email
                    [user.email],
                )
                
                messages.success(request, f"Admin {user.username} has been successfully created. An email has been sent with login credentials and a verification link.")
                return redirect('super_admin_dashboard')
            except Exception as e:
                print(f"DEBUG: Detailed error saving admin: {type(e).__name__}: {str(e)}")
                messages.error(request, f"Error creating admin: {str(e)}")
        else:
            # Log and display form errors
            print(f"DEBUG: Form validation errors: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
    
    # Create new form for GET requests
    form = CustomUserCreationForm(initial={'role': 'admin'})
    # Disable role field, don't just make it readonly
    form.fields['role'].widget.attrs['disabled'] = True
    
    return render(request, 'super_admin_dashboard.html', {'user_form': form})

@login_required
def add_staff(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden("You don't have permission to add staff members.")
    
    if request.method == 'POST':
        form = StaffCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.created_by = request.user  # ✅ FIXED
                user.is_email_verified = False
                user.generate_verification_token()
                user.save()
                
                # Send verification email
                verification_link = request.build_absolute_uri(
                    reverse('verify_email', args=[user.verification_token])
                )
                send_mail(
                    'Verify your email',
                    f'Click the link to verify your email: {verification_link}',
                    'your_email@example.com',
                    [user.email],
                )
                
                messages.success(request, 'Staff member added successfully.')
                return redirect('admin_dashboard')
            except Exception as e:
                messages.error(request, f'Error adding staff member: {str(e)}')
    else:
        form = StaffCreationForm()
    
    return render(request, 'add_staff.html', {'form': form})


@login_required
def add_warehouse_manager(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden("You don't have permission to add warehouse managers.")
    
    if request.method == 'POST':
        form = WarehouseForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.created_by = request.user  # ✅ FIXED
                user.is_email_verified = False
                user.generate_verification_token()
                user.save()
                
                # Send verification email
                verification_link = request.build_absolute_uri(
                    reverse('verify_email', args=[user.verification_token])
                )
                send_mail(
                    'Verify your email',
                    f'Click the link to verify your email: {verification_link}',
                    'your_email@example.com',
                    [user.email],
                )
                
                messages.success(request, 'Warehouse manager added successfully.')
                return redirect('admin_dashboard')
            except Exception as e:
                messages.error(request, f'Error adding warehouse manager: {str(e)}')
    else:
        form = WarehouseForm()
    
    return render(request, 'add_warehouse_manager.html', {'form': form})


@login_required
def approve_admin(request, admin_id):
    """View function to approve a pending admin"""
    if request.user.role != 'super_admin':
        return HttpResponseForbidden("You are not authorized to perform this action")
    
    if request.method == "POST":
        try:
            admin = get_object_or_404(CustomUser, id=admin_id, role='admin')
            admin.is_approved = True
            admin.save()
            
            # Log the activity
            ActivityLog.objects.create(
                admin=request.user,
                action=f"Approved admin account for {admin.username}"
            )
            
            # Send approval notification email
            try:
                send_mail(
                    'Admin Account Approved',
                    f"""
                    Dear {admin.username},
                    
                    Your admin account has been approved by the super administrator.
                    You can now log in to the admin dashboard.
                    
                    Thank you,
                    Super Admin
                    """,
                    'your_email@example.com',  # Replace with your email
                    [admin.email],
                    fail_silently=True
                )
            except Exception as e:
                print(f"Failed to send approval email: {str(e)}")
            
            messages.success(request, f"Admin {admin.username} has been approved successfully.")
        except Exception as e:
            messages.error(request, f"Error approving admin: {str(e)}")
        
    return redirect('super_admin_dashboard')

@login_required
def verify_admin(request, admin_id):
    """View function to verify an admin's account"""
    if request.user.role != 'super_admin':
        return HttpResponseForbidden("You are not authorized to perform this action")
    
    if request.method == "POST":
        try:
            admin = get_object_or_404(CustomUser, id=admin_id, role='admin')
            
            # First approve if not already approved
            if not admin.is_approved:
                admin.is_approved = True
            
            # Then verify
            admin.is_verified = True
            admin.is_email_verified = True  # Also mark email as verified
            admin.save()
            
            # Log the activity
            ActivityLog.objects.create(
                admin=request.user,
                action=f"Verified admin account for {admin.username}"
            )
            
            # Send verification confirmation email
            try:
                send_mail(
                    'Admin Account Verified',
                    f"""
                    Dear {admin.username},
                    
                    Your admin account has been verified by the super administrator.
                    You now have full access to the admin dashboard and all its features.
                    
                    Thank you,
                    Super Admin
                    """,
                    'your_email@example.com',  # Replace with your email
                    [admin.email],
                    fail_silently=True
                )
            except Exception as e:
                print(f"Failed to send verification email: {str(e)}")
            
            messages.success(request, f"Admin {admin.username} has been verified successfully.")
        except Exception as e:
            messages.error(request, f"Error verifying admin: {str(e)}")
        
    return redirect('super_admin_dashboard')

@login_required
def request_verification(request):
    if request.user.role == 'admin' and not request.user.is_verified:
        # Check if we have a verification message from the admin
        verification_message = request.POST.get('verification_message', '')
        
        # Set status to mark as needing approvaltion (change to True)
        request.user.is_approved = False
        
        # We don't have verification_request_date field, so we won't use it
        # Instead, we'll rely on model's last_login or Django's built-in timestamps
        request.user.save()
        
        # Log the verification request
        ActivityLog.objects.create(
            admin=request.user,
            action=f"Admin {request.user.username} requested account verification: {verification_message}"
        )
        
        # Try to notify super admins via email
        try:
            # Get all super admin emails
            super_admins = CustomUser.objects.filter(role='super_admin', is_active=True)
            super_admin_emails = [user.email for user in super_admins if user.email]
            
            if super_admin_emails:
                admin_details = f"""
                Username: {request.user.username}
                Email: {request.user.email}
                Date Requested: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
                Message: {verification_message if verification_message else 'No message provided'}
                """
                
                # Send email notification to super admins
                send_mail(
                    'Admin Verification Request',
                    f"An admin has requested account verification:\n\n{admin_details}\n\nPlease log in to approve this request.",
                    'your_email@example.com',  # Replace with your email
                    super_admin_emails,
                    fail_silently=True
                )
        except Exception as e:
            print(f"Failed to send email notification to super admins: {str(e)}")
        
        messages.success(request, "Your verification request has been sent to the super admin.")
        return redirect('admin_dashboard')
    
    # Show an error if the user is not an admin or already verified
    if request.user.role != 'admin':
        messages.error(request, "Only admin accounts can request verification.")
    elif request.user.is_verified:
        messages.info(request, "Your account is already verified.")
    
    return redirect('profile')

# Add a new view to show the request verification form
@login_required
def request_verification_form(request):
    if request.user.role != 'admin' or request.user.is_verified:
        return HttpResponseForbidden("You cannot request verification.")
    
    # Check if there's already a pending request - updated condition
    has_pending_request = request.user.is_approved == True and not request.user.is_verified
    
    return render(request, 'request_verification.html', {
        'has_pending_request': has_pending_request
    })

@login_required
def admin_management(request):
    if request.user.role != 'super_admin':
        return HttpResponseForbidden("You are not authorized to view this page")
    
    admins = CustomUser.objects.filter(role='admin')
    return render(request, 'admin_management.html', {'admins': admins})

@login_required
def edit_admin(request, admin_id):
    if request.user.role != 'super_admin':
        return HttpResponseForbidden("You are not authorized to perform this action")
    
    if request.method == "POST":
        admin = get_object_or_404(CustomUser, id=admin_id, role='admin')
        admin.username = request.POST.get('username', admin.username)
        admin.email = request.POST.get('email', admin.email)
        admin.save()
        messages.success(request, "Admin details updated successfully.")
        return redirect('super_admin_dashboard')

@login_required
def delete_admin(request, admin_id):
    if request.user.role != 'super_admin':
        return HttpResponseForbidden("You are not authorized to perform this action")
    
    if request.method == "POST":
        admin = get_object_or_404(CustomUser, id=admin_id, role='admin')
        admin.delete()
        messages.success(request, "Admin deleted successfully.")
        return redirect('super_admin_dashboard')

@login_required
def change_admin_password(request, admin_id):
    if request.user.role != 'super_admin':
        return HttpResponseForbidden("You don't have permission to change admin passwords.")
    
    admin = get_object_or_404(CustomUser, id=admin_id, role='admin')
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('super_admin_dashboard')
        
        admin.set_password(new_password)
        admin.save()
        
        ActivityLog.objects.create(
            admin=request.user,
            action=f"Changed password for admin {admin.username}"
        )
        
        messages.success(request, f"Password changed successfully for admin {admin.username}")
        return redirect('super_admin_dashboard')
    
    return HttpResponseBadRequest("Invalid request method")

@login_required
def toggle_admin_status(request, admin_id):
    if request.user.role != 'super_admin':
        return HttpResponseForbidden("You don't have permission to toggle admin status.")
    
    admin = get_object_or_404(CustomUser, id=admin_id, role='admin')
    
    # Toggle the is_active status
    admin.is_active = not admin.is_active
    admin.save()
    
    # Log the activity
    action = "Activated" if admin.is_active else "Deactivated"
    ActivityLog.objects.create(
        admin=request.user,
        action=f"{action} admin account {admin.username}"
    )
    
    messages.success(request, f"Admin {admin.username} has been {action.lower()} successfully.")
    return redirect('super_admin_dashboard')

def landing_page(request):
    return render(request, 'landing.html')

# Profile view - Displays user profile and recent orders if they are a customer
@login_required
def profile_view(request):
    recent_orders = []
    if request.user.role == 'customer':
        recent_orders = Order.objects.filter(customer=request.user).order_by('-created_at')[:5]
    
    return render(request, 'profile.html', {
        'user': request.user,
        'recent_orders': recent_orders
    })

@login_required
def account_settings(request):
    if request.method == 'POST':
        # Update user information
        try:
            user = request.user
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.email = request.POST.get('email', user.email)
            user.phone_number = request.POST.get('phone_number', user.phone_number) if hasattr(user, 'phone_number') else None
            
            # Save other profile fields if they exist
            if 'address' in request.POST:
                user.address = request.POST.get('address')
            if 'city' in request.POST:
                user.city = request.POST.get('city')
            if 'state' in request.POST:
                user.state = request.POST.get('state')
            if 'country' in request.POST:
                user.country = request.POST.get('country')
            if 'zip_code' in request.POST:
                user.zip_code = request.POST.get('zip_code')
            
            user.save()
            messages.success(request, 'Your account information has been updated successfully.')
            return redirect('account_settings')
        except Exception as e:
            messages.error(request, f'Error updating account: {str(e)}')
    
    return render(request, 'account_settings.html', {'user': request.user})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Important: update the session to prevent logging out
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'change_password.html', {'form': form})

@login_required
def super_admin_profile(request):
    if request.user.role != 'super_admin':
        return HttpResponseForbidden("You are not authorized to view this page")
    
    context = {
        'user': request.user,
        'recent_activities': ActivityLog.objects.filter(admin=request.user).order_by('-timestamp')[:10]
    }
    return render(request, 'super_admin_profile.html', context)

@login_required
def assign_warehouse_manager(request, warehouse_id):
    if request.user.role != 'admin':
        return HttpResponseForbidden("You are not authorized to perform this action")
    
    if request.method == "POST":
        manager_id = request.POST.get('manager_id')
        warehouse = get_object_or_404(Warehouse, id=warehouse_id)
        
        try:
            if (manager_id):
                manager = get_object_or_404(CustomUser, id=manager_id, role='warehouse_manager')
                warehouse.manager = manager
                warehouse.save()
                
                # Log the activity
                ActivityLog.objects.create(
                    admin=request.user,
                    action=f"Assigned manager {manager.username} to warehouse {warehouse.name}"
                )
                messages.success(request, f'Successfully assigned {manager.username} to {warehouse.name}')
            else:
                warehouse.manager = None
                warehouse.save()
                messages.success(request, f'Successfully unassigned manager from {warehouse.name}')
                
        except Exception as e:
            messages.error(request, f'Error assigning manager: {str(e)}')
        return redirect('admin_dashboard')
    
    return render(request, 'assign_warehouse_manager.html', {'warehouse_id': warehouse_id})

@login_required
def warehouse_products(request, warehouse_id):
    if request.user.role not in ['admin', 'warehouse_manager']:
        return HttpResponseForbidden("You are not authorized to view this page")
    
    warehouse = get_object_or_404(Warehouse, id=warehouse_id)
    products = Product.objects.filter(warehouse=warehouse)
    
    context = {
        'warehouse': warehouse,
        'products': products
    }
    
    return render(request, 'warehouse_products.html', context)

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email)
            # Generate password reset token
            token = get_random_string(length=32)
            user.reset_password_token = token
            user.reset_password_expires = timezone.now() + timezone.timedelta(hours=24)
            user.save()
            
            # Send reset email
            reset_link = request.build_absolute_uri(
                reverse('reset_password', args=[token])
            )
            send_mail(
                'Reset Your Password',
                f'Click the link to reset your password: {reset_link}\nThis link will expire in 24 hours.',
                'your_email@example.com',  # Replace with your email
                [user.email],
            )
            messages.success(request, 'Password reset link has been sent to your email.')
            return redirect('login')
        except CustomUser.DoesNotExist:
            messages.error(request, 'No user found with this email address.')
    return render(request, 'forgot_password.html')

def reset_password(request, token):
    try:
        # Debug log to see what's happening
        print(f"DEBUG: Attempting password reset with token: {token}")
        
        user = CustomUser.objects.get(
            reset_password_token=token,
            reset_password_expires__gt=timezone.now()
        )
        
        print(f"DEBUG: Found user: {user.username} with email: {user.email}")
        
        if request.method == 'POST':
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            
            print(f"DEBUG: Received password reset POST request")
            
            if password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'reset_password.html')
            
            # Reset the password
            user.set_password(password)
            user.reset_password_token = None
            user.reset_password_expires = None
            user.save()
            
            print(f"DEBUG: Password reset successful for user: {user.username}")
            messages.success(request, 'Your password has been reset successfully. You can now login.')
            
            # Explicitly use an HttpResponseRedirect for more reliable redirection
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect(reverse('login'))
            
        return render(request, 'reset_password.html')
    except CustomUser.DoesNotExist:
        print(f"DEBUG: Invalid or expired reset token: {token}")
        messages.error(request, 'Invalid or expired reset link.')
        return redirect('login')
    except Exception as e:
        print(f"DEBUG: Error during password reset: {str(e)}")
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('login')


@login_required
def add_user_page(request):
    """View for rendering the add user page template."""
    if request.user.role != 'admin':
        return HttpResponseForbidden("You are not authorized to perform this action")
    
    return render(request, 'add_user.html')

@login_required
def edit_warehouse(request, warehouse_id):
    """View function to edit a warehouse's details"""
    if request.user.role != 'admin':
        return HttpResponseForbidden("You are not authorized to perform this action")
    
    warehouse = get_object_or_404(Warehouse, id=warehouse_id)
    
    if request.method == 'POST':
        form = WarehouseForm(request.POST, instance=warehouse)
        if form.is_valid():
            form.save()
            # Log the activity
            ActivityLog.objects.create(
                admin=request.user,
                action=f"Updated warehouse: {warehouse.name}"
            )
            messages.success(request, f'Warehouse "{warehouse.name}" updated successfully!')
            return redirect('manage_warehouses')
    else:
        form = WarehouseForm(instance=warehouse)
    
    return render(request, 'edit_warehouse.html', {'form': form, 'warehouse': warehouse})

@login_required
def delete_warehouse(request, warehouse_id):
    """View function to delete a warehouse"""
    if request.user.role != 'admin':
        return HttpResponseForbidden("You are not authorized to perform this action")
    
    warehouse = get_object_or_404(Warehouse, id=warehouse_id)
    warehouse_name = warehouse.name
    
    if request.method == 'POST':
        try:
            # Check if products are associated with this warehouse
            associated_products = Product.objects.filter(warehouse=warehouse)
            product_count = associated_products.count()
            
            # If products exist, reassign them to a default warehouse before deletion
            if (product_count > 0):
                # Find or create a suitable default warehouse
                default_warehouse, created = Warehouse.objects.get_or_create(
                    name="Default Warehouse",
                    defaults={
                        'location': 'Default Location',
                        'handles_expiring': True  # Set to True to handle all types of products
                    }
                )
                
                # Make sure we don't reassign to the same warehouse we're deleting
                if default_warehouse.id == warehouse.id:
                    # Find another warehouse or create a new one with a different name
                    default_warehouse, created = Warehouse.objects.get_or_create(
                        name="Backup Warehouse",
                        defaults={
                            'location': 'Default Location',
                            'handles_expiring': True
                        }
                    )
                
                # Reassign all products to the default warehouse
                associated_products.update(warehouse=default_warehouse)
                
                # Log the reassignment
                ActivityLog.objects.create(
                    admin=request.user,
                    action=f"Reassigned {product_count} products from warehouse '{warehouse_name}' to '{default_warehouse.name}'"
                )
                
                messages.info(
                    request, 
                    f"{product_count} products from warehouse '{warehouse_name}' have been reassigned to '{default_warehouse.name}'.",
                )
            
            # Now delete the warehouse
            warehouse.delete()
            
            # Log the activity
            ActivityLog.objects.create(
                admin=request.user,
                action=f"Deleted warehouse: {warehouse_name}"
            )
            
            messages.success(request, f'Warehouse "{warehouse_name}" deleted successfully!')
        except Exception as e:
            print(f"ERROR DELETING WAREHOUSE: {str(e)}")
            messages.error(request, f'Error deleting warehouse: {str(e)}')
        
        # Always redirect back to manage_warehouses, even if there's an error
        return redirect('manage_warehouses')
    
    # For GET requests, render the confirmation page
    return render(request, 'delete_warehouse.html', {'warehouse': warehouse})

@login_required
def assign_staff_to_order(request, order_id):
    if request.user.role != 'warehouse_manager':
        return HttpResponseForbidden("You are not authorized to perform this action")

    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        staff_id = request.POST.get('staff_id')
        try:
            staff = CustomUser.objects.get(id=staff_id, role='staff')
            order.assigned_staff = staff
            order.save()
            messages.success(request, f"Staff {staff.username} assigned to order {order.order_number}")
        except CustomUser.DoesNotExist:
            messages.error(request, "Selected staff member does not exist.")
        except Exception as e:
            messages.error(request, f"Error assigning staff: {str(e)}")

        return redirect('warehouse_orders')

    staff_members = CustomUser.objects.filter(role='staff', is_active=True)
    return render(request, 'assign_staff_to_order.html', {
        'order': order,
        'staff_members': staff_members
    })


@login_required
def edit_category(request, category_id):
    """View function to edit a category"""
    if request.user.role != 'admin':
        return HttpResponseForbidden("You are not authorized to perform this action")
    
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            # Get the expires field value (checkbox)
            expires = request.POST.get('expires') == 'on'
            
            print(f"CATEGORY DATA - Name: '{name}', Description: '{description}', Expires: {expires}")
            
            if not name:
                print("ERROR: Category name is empty")
                return JsonResponse({
                    'success': False,
                    'error': 'Category name cannot be empty'
                }, status=400)
            
            # Check if another category with this name exists (excluding current category)
            # FIX: Changed (name) to =name
            if Category.objects.filter(name__iexact=name).exclude(id=category_id).exists():
                print(f"ERROR: Category '{name}' already exists")
                return JsonResponse({
                    'success': False,
                    'error': f'Category "{name}" already exists'
                }, status=400)
            
            # Update category
            category.name = name
            category.description = description
            category.expires = expires
            category.save()
            
            # Log the activity
            ActivityLog.objects.create(
                admin=request.user,
                action=f"Updated category: {category.name} (Expires: {expires})"
            )
            messages.success(request, f'Category "{category.name}" updated successfully!')
            return JsonResponse({
                'success': True,
                'message': f'Category "{category.name}" updated successfully!'
            })
            
        except Exception as e:
            messages.error(request, f'Error updating category: {str(e)}')
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=405)

@login_required
def manage_categories(request):
    """View function to list all categories"""
    if request.user.role != 'admin':
        return HttpResponseForbidden("You are not authorized to view this page")
    
    categories = Category.objects.all()
    return render(request, 'manage_categories.html', {'categories': categories})

# Cart Views
@login_required
def view_cart(request):
    """View to display the user's cart contents"""
    # Get or create cart for the user
    cart, created = Cart.objects.get_or_create(user=request.user)
    # Calculate total price
    total_price = sum(item.product.price * item.quantity for item in cart.items.all())
    context = {
        'cart': cart,
        'cart_items': cart.items.all().select_related('product'),
        'total_price': total_price
    }
    return render(request, 'cart.html', context)

@login_required
@require_POST
def add_to_cart(request):
    """View to add a product to the user's cart"""
    product_id = request.POST.get('product_id')
    quantity = int(request.POST.get('quantity', 1))
    
    if not product_id:
        return JsonResponse({'success': False, 'message': 'Product ID is required'}, status=400)
    
    try:
        product = Product.objects.get(id=product_id)
        
        # Get or create the user's cart
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        # Check if product already exists in cart
        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': 0}  # Initialize with 0 to handle stock check next
        )
        
        # Calculate the new total quantity
        new_total_quantity = cart_item.quantity + quantity
        
        # Check if there's enough stock for the combined quantity 
        if product.stock < new_total_quantity:
            return JsonResponse({
                'success': False,
                'message': f'Not enough stock available. Only {product.stock} available.',
                'available_stock': product.stock,
                'current_cart_quantity': cart_item.quantity
            }, status=400)
        
        # Now update the quantity
        cart_item.quantity = new_total_quantity
        cart_item.save()
            
        # Calculate new cart totals
        total_items = cart.total_items
        total_price = cart.total_price
        
        return JsonResponse({
            'success': True,
            'message': f'Added {quantity} {product.name} to your cart',
            'cart_total_items': total_items,
            'cart_total_price': total_price,
            'item_quantity': cart_item.quantity,
            'item_subtotal': cart_item.subtotal
        })
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Product not found'}, status=404)
    except Exception as e:
        print(f"ERROR in add_to_cart: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
@require_POST
def update_cart_item(request):
    """View to update the quantity of an item in the cart"""
    cart_item_id = request.POST.get('cart_item_id')
    new_quantity = int(request.POST.get('quantity', 1))
    redirect_url = request.POST.get('redirect', None)  # Get optional redirect URL
    
    if not cart_item_id:
        return JsonResponse({'success': False, 'message': 'Cart item ID is required'}, status=400)
    
    try:
        # Get the cart item with a select_related to the product to reduce DB queries
        cart_item = CartItem.objects.select_related('product').get(id=cart_item_id, cart__user=request.user)
        
        if new_quantity <= 0:
            # If quantity is 0 or less, remove the item
            cart_item.delete()
            message = 'Item removed from cart'
            
            # Get new cart totals after deletion
            cart = Cart.objects.get(user=request.user)
            total_items = cart.total_items
            total_price = float(cart.total_price) if cart.total_price else 0.0
            
            # If redirect parameter is provided, include it in response
            if redirect_url:
                return JsonResponse({
                    'success': True,
                    'message': message,
                    'redirect': redirect_url,
                    'cart_total_items': total_items,
                    'cart_total_price': total_price,
                    'item_subtotal': 0
                })
                
            return JsonResponse({
                'success': True,
                'message': message,
                'cart_total_items': total_items,
                'cart_total_price': total_price,
                'item_subtotal': 0
            })
        
        # Check if there's enough stock for the new quantity
        if cart_item.product.stock < new_quantity:
            return JsonResponse({
                'success': False,
                'message': f'Not enough stock available. Only {cart_item.product.stock} available.',
                'available_stock': cart_item.product.stock
            }, status=400)
        
        # Update the quantity
        previous_quantity = cart_item.quantity
        cart_item.quantity = new_quantity
        cart_item.save()
        
        # Recalculate subtotal after save - Ensure it's a float
        subtotal = float(cart_item.product.price * new_quantity)
        
        # Get new cart totals
        cart = request.user.cart
        total_items = cart.total_items
        total_price = float(cart.total_price) if cart.total_price else 0.0
        
        # Log the update for debugging
        print(f"Cart item updated: id={cart_item_id}, product={cart_item.product.name}, " +
              f"quantity: {previous_quantity} → {new_quantity}, subtotal=${subtotal}")
        
        return JsonResponse({
            'success': True,
            'message': 'Cart updated successfully',
            'cart_total_items': total_items,
            'cart_total_price': total_price,
            'item_subtotal': subtotal
        })
    except CartItem.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'message': 'Cart item not found'
        }, status=404)
    except Exception as e:
        print(f"Error in update_cart_item: {str(e)}")
        # Log the exception for debugging
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False, 
            'message': f'Error updating cart: {str(e)}'
        }, status=500)

@login_required
@require_POST
def remove_from_cart(request):
    """View to remove an item from the cart"""
    cart_item_id = request.POST.get('cart_item_id')
    redirect_to_dashboard = request.POST.get('redirect_to_dashboard', 'false').lower() == 'true'
    
    if not cart_item_id:
        return JsonResponse({'success': False, 'message': 'Cart item ID is required'}, status=400)
    
    try:
        cart_item = CartItem.objects.get(id=cart_item_id, cart__user=request.user)
        product_name = cart_item.product.name
        cart_item.delete()
        
        # Get new cart totals
        cart = request.user.cart
        total_items = cart.total_items
        total_price = cart.total_price
        
        response_data = {
            'success': True,
            'message': f'{product_name} removed from your cart',
            'cart_total_items': total_items,
            'cart_total_price': total_price
        }
        
        # If requested to redirect to dashboard
        if redirect_to_dashboard:
            response_data['redirect'] = reverse('order_list')
        
        return JsonResponse(response_data)
    except CartItem.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Cart item not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
@require_POST
def clear_cart(request):
    """View to remove all items from the cart"""
    try:
        if hasattr(request.user, 'cart'):
            request.user.cart.items.all().delete()
        return JsonResponse({
            'success': True,
            'message': 'Cart cleared successfully',
            'cart_total_items': 0,
            'cart_total_price': 0
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

# Wishlist Views
@login_required
def view_wishlist(request):
    """View to display the user's wishlist contents"""
    # Get or create wishlist for the user
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    context = {
        'wishlist': wishlist,
        'wishlist_items': wishlist.items.all().select_related('product')
    }
    return render(request, 'wishlist.html', context)

@login_required
@require_POST
def add_to_wishlist(request):
    """View to add a product to the user's wishlist"""
    product_id = request.POST.get('product_id')
    
    if not product_id:
        return JsonResponse({'success': False, 'message': 'Product ID is required'}, status=400)
    
    try:
        product = Product.objects.get(id=product_id)
        
        # Get or create the user's wishlist
        wishlist,created = Wishlist.objects.get_or_create(user=request.user)
        
        # Check if product already exists in wishlist
        _, item_created = WishlistItem.objects.get_or_create(
            wishlist=wishlist,
            product=product
        )
        
        # Success message based on whether item was added or already existed
        message = f'Added {product.name} to your wishlist' if item_created else f'{product.name} is already in your wishlist'
        
        # Get total wishlist items
        total_items = wishlist.items.count()
        
        return JsonResponse({
            'success': True,
            'message': message,
            'wishlist_total_items': total_items,
            'added': item_created
        })
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Product not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
def staff_deliveries(request):
    if request.user.role != 'staff':
        return HttpResponseForbidden("You are not authorized to view this page")

    # Assuming `Order` model has a ForeignKey to staff like `assigned_staff`
    deliveries = Order.objects.filter(assigned_staff=request.user).order_by('-created_at')

    return render(request, 'staff_deliveries.html', {'deliveries': deliveries})


@login_required
@require_POST
def remove_from_wishlist(request):
    """View to remove an item from the wishlist"""
    wishlist_item_id = request.POST.get('wishlist_item_id')
    
    if not wishlist_item_id:
        return JsonResponse({'success': False, 'message': 'Wishlist item ID is required'}, status=400)
    
    try:
        wishlist_item = WishlistItem.objects.get(id=wishlist_item_id, wishlist__user=request.user)
        product_name = wishlist_item.product.name
        wishlist_item.delete()
        
        # Get total wishlist items
        total_items = request.user.wishlist.items.count()
        
        return JsonResponse({
            'success': True,
            'message': f'{product_name} removed from your wishlist',
            'wishlist_total_items': total_items
        })
    except WishlistItem.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Wishlist item not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
@require_POST
def move_to_cart(request):
    """View to move an item from the wishlist to the cart"""
    wishlist_item_id = request.POST.get('wishlist_item_id')
    quantity = int(request.POST.get('quantity', 1))
    
    if not wishlist_item_id:
        return JsonResponse({'success': False, 'message': 'Wishlist item ID is required'}, status=400)
    
    try:
        # Get the wishlist item
        wishlist_item = WishlistItem.objects.get(id=wishlist_item_id, wishlist__user=request.user)
        product = wishlist_item.product
        
        # Check if there's enough stock
        if product.stock < quantity:
            return JsonResponse({
                'success': False,
                'message': f'Not enough stock available. Only {product.stock} available.'
            }, status=400)
        
        # Get or create the cart
        cart, _ = Cart.objects.get_or_create(user=request.user)
        
        # Add to cart or update if already exists
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity = F('quantity') + quantity
            cart_item.save()
        
        # Remove from wishlist
        wishlist_item.delete()
        
        # Get updated counts
        wishlist_count = request.user.wishlist.items.count()
        cart_count = cart.items.count()
        
        return JsonResponse({
            'success': True,
            'message': f'Moved {product.name} from wishlist to cart',
            'wishlist_total_items': wishlist_count,
            'cart_total_items': cart_count
        })
    except WishlistItem.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Wishlist item not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

# Modify the existing order_list view to include cart and wishlist counts
@login_required
def order_list(request):
    if request.user.role == 'customer':
        orders = Order.objects.filter(customer=request.user)
        products = Product.objects.all()
        # Get or create cart and wishlist for displaying counts
        cart, _ = Cart.objects.get_or_create(user=request.user)
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        context = {
            'orders': orders,
            'products': products,
            'cart': cart,
            'wishlist': wishlist
        }
        return render(request, 'order_list.html', context)
    elif request.user.role == 'warehouse_manager':
        orders = Order.objects.all()
        return render(request, 'order_list.html', {'orders': orders})
    else:
        return HttpResponseForbidden("You are not authorized to view this page")

@login_required
def checkout(request):
    """View to process checkout from cart items"""
    # Ensure user is a customer
    if request.user.role != 'customer':
        return HttpResponseForbidden("Only customers can checkout")
    
    # Get user's cart
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all().select_related('product')
    except Cart.DoesNotExist:
        messages.error(request, "You don't have an active cart")
        return redirect('order_list')
    
    # Check if cart is empty
    if not cart_items.exists():
        messages.error(request, "Your cart is empty")
        return redirect('view_cart')
    
    # Calculate total amount
    total_amount = sum(item.product.price * item.quantity for item in cart_items)
    
    if request.method == "POST":
        # Process the checkout
        try:
            # Begin transaction
            with transaction.atomic():
                # Create order with only the fields we know exist in the model
                order = Order.objects.create(
                    order_number=str(uuid.uuid4()),
                    customer=request.user,
                    total_amount=total_amount,
                    status='pending'
                )
                
                # Save shipping details separately in session for future use
                shipping_info = {
                    'shipping_address': request.POST.get('shipping_address'),
                    'shipping_city': request.POST.get('shipping_city'),
                    'shipping_state': request.POST.get('shipping_state'),
                    'shipping_country': request.POST.get('shipping_country'),
                    'shipping_zip': request.POST.get('shipping_zip'),
                    'first_name': request.POST.get('first_name'),
                    'last_name': request.POST.get('last_name'),
                    'email': request.POST.get('email'),
                    'phone': request.POST.get('phone')
                }
                
                # Store shipping info in session
                request.session['last_shipping_info'] = shipping_info
                
                # Check for Khalti payment token
                khalti_token = request.POST.get('khalti_token')
                payment_method = request.POST.get('payment_method', 'cash_on_delivery')
                
                # Save payment method to order
                try:
                    # Update order with payment information
                    order.payment_method = payment_method
                    if khalti_token:
                        order.payment_status = 'paid'
                        order.payment_details = khalti_token
                    else:
                        order.payment_status = 'pending'
                    order.save()
                except Exception as e:
                    print(f"WARNING: Could not save payment details to order: {e}")
                
                # Try to update shipping fields if they exist in the model
                try:
                    # Get the order field names to check if shipping fields exist
                    order_fields = [f.name for f in Order._meta.get_fields()]
                    
                    # Update only fields that exist in the model
                    for field, value in shipping_info.items():
                        if field in order_fields and value:
                            setattr(order, field, value)
                    
                    # Save changes if any
                    order.save()
                except Exception as e:
                    # Log the error but continue with order creation
                    print(f"WARNING: Could not save shipping details to order: {e}")
                
                # Create order items from cart items
                for cart_item in cart_items:
                    # Check if enough stock is available
                    if cart_item.product.stock < cart_item.quantity:
                        messages.error(
                            request, 
                            f"Not enough stock for {cart_item.product.name}. Only {cart_item.product.stock} available."
                        )
                        return redirect('view_cart')
                    
                    # Create order item
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        price=cart_item.product.price
                    )
                    
                    # Update product stock
                    cart_item.product.stock -= cart_item.quantity
                    cart_item.product.save()
                
                # Clear the cart
                cart.items.all().delete()
                
                # Log the activity - FIX: Use admin field instead of user
                ActivityLog.objects.create(
                    admin=request.user,  # Use admin field for the user
                    action=f"Placed order #{order.order_number} for ${order.total_amount} via {payment_method}"
                )
                
                payment_status_msg = " Payment completed successfully!" if khalti_token else ""
                messages.success(request, f"Your order has been placed successfully!{payment_status_msg}")
                return redirect('order_detail', order_id=order.id)
        except Exception as e:
            messages.error(request, f"Error processing checkout: {str(e)}")
            return redirect('view_cart')
    
    # For GET requests, show checkout form
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_amount': total_amount
    }
    
    return render(request, 'checkout.html', context)

@login_required
def product_catalog(request):
    """View to display products for customers to browse"""
    # Ensure user is a customer
    if request.user.role != 'customer':
        return HttpResponseForbidden("You are not authorized to view this page")
    
    # Get filter parameters from request
    category_id = request.GET.get('category')
    search_query = request.GET.get('q')
    sort_by = request.GET.get('sort', 'name')  # Default sort by name
    
    # Start with all products that have stock
    products = Product.objects.filter(stock__gt=0)
    
    # Apply category filter if provided
    if category_id:
        try:
            products = products.filter(category_id=int(category_id))
        except (ValueError, TypeError):
            pass  # Invalid category_id, ignore filter
    
    # Apply search filter if provided
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Apply sorting
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-id')  # Assuming newer products have higher IDs
    else:  # Default to name
        products = products.order_by('name')
    
    # Get all categories for the filter dropdown
    categories = Category.objects.all()
    
    # Get user's cart and wishlist for convenience
    cart, _ = Cart.objects.get_or_create(user=request.user)
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    
    # Create a mapping of product IDs that are in the wishlist for easy checking in template
    wishlist_product_ids = set(wishlist.items.values_list('product_id', flat=True))
    
    context = {
        'products': products,
        'categories': categories,
        'selected_category': category_id,
        'search_query': search_query,
        'sort_by': sort_by,
        'cart': cart,
        'wishlist': wishlist,
        'wishlist_product_ids': wishlist_product_ids,
    }
    
    return render(request, 'product_catalog.html', context)

# Add a new endpoint to get category details
@login_required
def get_category_details(request, category_id):
    """API endpoint to get category details including expires field"""
    if request.user.role not in ['admin', 'warehouse_manager']:
        return HttpResponseForbidden("You are not authorized to perform this action")
    
    try:
        category = get_object_or_404(Category, id=category_id)
        data = {
            'id': category.id,
            'name': category.name,
            'description': category.description or '',
            'expires': category.expires
        }
        return JsonResponse(data)
    except Exception as e:
        print(f"DEBUG: Error fetching category details: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def warehouse_product_count(request, warehouse_id):
    """API endpoint to get the count of products in a warehouse"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        warehouse = get_object_or_404(Warehouse, id=warehouse_id)
        count = Product.objects.filter(warehouse=warehouse).count()
        return JsonResponse({'count': count})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def update_stock(request, product_id):
    """View function to update a product's stock level"""
    if request.user.role != 'warehouse_manager':
        return HttpResponseForbidden("You are not authorized to perform this action")
    
    if request.method == 'POST':
        try:
            product = get_object_or_404(Product, id=product_id)
            stock_change = int(request.POST.get('stock_change'))
            
            # Update the stock
            product.stock += stock_change
            
            # Ensure stock doesn't go below zero
            if product.stock < 0:
                product.stock = 0
                
            product.save()
            
            # Log the activity
            ActivityLog.objects.create(
                admin=request.user,
                action=f"Updated stock for {product.name} by {stock_change} units (New stock: {product.stock})"
            )
            messages.success(request, f"Stock updated successfully for {product.name}")
        except Exception as e:
            messages.error(request, f"Error updating stock: {str(e)}")
    
    return redirect('staff_inventory_management')

@login_required
def order_dashboard(request):
    """View for order management dashboard"""
    if request.user.role not in ['admin', 'warehouse_manager', 'super_admin']:
        return HttpResponseForbidden("You are not authorized to view this page")
    
    # Get all orders with their status
    all_orders = Order.objects.all().select_related('customer')
    
    # Get status filter from query params
    status_filter = request.GET.get('status', '')
    
    # Apply status filter if provided
    filtered_orders = all_orders
    if status_filter and status_filter != 'all':
        filtered_orders = all_orders.filter(status=status_filter)
    
    # Order by most recent first
    filtered_orders = filtered_orders.order_by('-created_at')
    
    # Calculate order statistics
    context = {
        'recent_orders': filtered_orders[:10],  # Show 10 most recent orders
        'total_orders': all_orders.count(),
        'pending_orders': all_orders.filter(status='pending').count(),
        'processing_orders': all_orders.filter(status='processing').count(),
        'shipped_orders': all_orders.filter(status='shipped').count(),
        'delivered_orders': all_orders.filter(status='delivered').count(),
        'cancelled_orders': all_orders.filter(status='cancelled').count(),
        'current_status': status_filter or 'all'
    }
    
    return render(request, 'order_dashboard.html', context)

@login_required
@require_POST
def verify_khalti_payment(request):
    """Verify Khalti payment with Khalti server"""
    if request.user.role != 'customer':
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
    
    try:
        # Parse the request data
        payload = json.loads(request.body)
        token = payload.get('token')
        amount = payload.get('amount')
        
        if not token or not amount:
            return JsonResponse({
                'success': False,
                'message': 'Invalid payment data'
            }, status=400)
        
        # Prepare verification data
        verification_data = {
            'token': token,
            'amount': amount
        }
        
        # Replace with your actual Khalti secret key
        headers = {
            'Authorization': "live_secret_key_68791341fdd94846a146f0457ff7b455"
        }
        
        # Verify with Khalti server
        response = requests.post(
            'https://khalti.com/api/v2/payment/verify/',
            data=verification_data,
            headers=headers
        )
        
        # Process the response
        if response.status_code == 200:
            # Payment verified successfully
            verification_response = response.json()
            
            # Log the activity
            ActivityLog.objects.create(
                admin=request.user,
                action=f"Verified Khalti payment of NPR {amount/100} with token {token[:10]}..."
            )
            
            return JsonResponse({
                'success': True,
                'data': verification_response
            })
        else:
            # Payment verification failed
            error_data = response.json()
            return JsonResponse({
                'success': False,
                'message': error_data.get('detail', 'Payment verification failed'),
                'error': error_data
            })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False, 
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': str(e)
        }, status=500)

@login_required
def staff_dashboard(request):
    """
    Dashboard view for staff members showing assigned orders, deliveries, and inventory status.
    
    This view displays:
    - Recent assigned orders
    - Pending deliveries
    - Completed deliveries
    - Low stock products
    - Order statistics
    """
    if request.user.role != 'staff':
        return HttpResponseForbidden("You are not authorized to view this page")
    
    try:
        # Get the admin who created this staff member
        created_by = request.user.created_by
        
        # Get staff's order data
        staff_orders = get_staff_order_data(request.user)
        
        # Get low stock products that need attention
        low_stock_products = get_low_stock_products()
        
        context = {
            'recent_assigned_orders': staff_orders['recent_orders'],
            'pending_deliveries': staff_orders['pending_deliveries'],
            'completed_deliveries': staff_orders['completed_deliveries'],
            'low_stock_products': low_stock_products,
            'total_assigned_orders': staff_orders['total_count'],
            'pending_deliveries_count': staff_orders['pending_count'],
            'completed_deliveries_count': staff_orders['completed_count'],
            'created_by': created_by
        }
        
        return render(request, 'staff_dashboard.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading dashboard: {str(e)}")
        return render(request, 'staff_dashboard.html', {'error': str(e)})


def get_staff_order_data(staff_user):
    """
    Helper function to get order data for a staff member.
    
    Args:
        staff_user: The staff user object
    
    Returns:
        dict: Dictionary containing order data
    """
    # Get orders assigned to this staff member
    assigned_orders = Order.objects.filter(assigned_to=staff_user).order_by('-created_at')
    recent_orders = assigned_orders[:5]
    
    # Get pending deliveries (orders in shipped status assigned to this staff)
    pending_deliveries = assigned_orders.filter(status='shipped')
    
    # Get recently completed deliveries
    completed_deliveries = assigned_orders.filter(status='delivered').order_by('-created_at')[:5]
    
    # Calculate order statistics
    total_count = assigned_orders.count()
    pending_count = pending_deliveries.count()
    completed_count = assigned_orders.filter(status='delivered').count()
    
    return {
        'recent_orders': recent_orders,
        'pending_deliveries': pending_deliveries,
        'completed_deliveries': completed_deliveries,
        'total_count': total_count,
        'pending_count': pending_count,
        'completed_count': completed_count
    }


def get_low_stock_products():
    """
    Helper function to get products with stock at or below minimum level.
    
    Returns:
        QuerySet: Products with low stock
    """
    return Product.objects.filter(stock__lte=F('min_stock'))

@login_required
def staff_order_management(request):
    """View for staff to manage orders"""
    if request.user.role != 'staff':
        return HttpResponseForbidden("You are not authorized to view this page")
    
    # Get status filter from query params
    status_filter = request.GET.get('status', '')
    
    # Get all orders assigned to this staff
    assigned_deliveries = Order.objects.filter(assigned_to=request.user)
    
    # Apply status filter if provided
    if status_filter and status_filter != 'all':
        assigned_deliveries = assigned_deliveries.filter(status=status_filter)
    else:
        # Default to show orders that need action (pending, processing, shipped)
        assigned_deliveries = assigned_deliveries.filter(
            status__in=['pending', 'processing', 'shipped']
        )
    
    # Order by most recent first
    assigned_deliveries = assigned_deliveries.order_by('-created_at')
    
    context = {
        'assigned_deliveries': assigned_deliveries,
        'assigned_deliveries_count': assigned_deliveries.count(),
        'current_status': status_filter or 'active',
        'pending_count': Order.objects.filter(assigned_to=request.user, status='pending').count(),
        'processing_count': Order.objects.filter(assigned_to=request.user, status='processing').count(),
        'shipped_count': Order.objects.filter(assigned_to=request.user, status='shipped').count(),
        'delivered_count': Order.objects.filter(assigned_to=request.user, status='delivered').count()
    }
    
    return render(request, 'staff_deliveries.html', context)

@login_required
def export_billing(request, order_id=None):
    """View to export billing information as PDF or CSV"""
    if request.user.role != 'customer' and not request.user.is_staff:
        return HttpResponseForbidden("You are not authorized to perform this action")
    
    # Determine what to export based on parameters
    export_type = request.GET.get('type', 'pdf')
    
    try:
        # If specific order is requested, export just that order
        if order_id:
            order = get_object_or_404(Order, id=order_id)
            
            # Check permissions (only the customer or staff/managers can export)
            if request.user.role == 'customer' and order.customer != request.user:
                return HttpResponseForbidden("You cannot access this order")
                
            orders = [order]
            filename = f"order_{order.order_number}"
        else:
            # Otherwise export all orders for the customer
            if request.user.role == 'customer':
                orders = Order.objects.filter(customer=request.user).order_by('-created_at')
                filename = f"orders_{request.user.username}"
            else:
                # For staff/managers, they need a customer_id param
                customer_id = request.GET.get('customer_id')
                if not customer_id:
                    return HttpResponseBadRequest("Customer ID is required")
                
                customer = get_object_or_404(CustomUser, id=customer_id, role='customer')
                orders = Order.objects.filter(customer=customer).order_by('-created_at')
                filename = f"orders_{customer.username}"
        
        if export_type == 'csv':
            return export_orders_csv(orders, filename)
        else:
            return export_orders_pdf(orders, filename)
            
    except Exception as e:
        messages.error(request, f"Error exporting billing information: {str(e)}")
        return redirect('order_list')

def export_orders_pdf(orders, filename):
    """Helper function to generate PDF for orders"""
    import io
    from django.http import FileResponse
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch
    from reportlab.lib.pagesizes import letter
    
    # Create a file-like buffer to receive PDF data
    buffer = io.BytesIO()
    
    # Create the PDF object, using the buffer as its "file"
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Set up document
    y_position = 750  # Starting y position on page
    p.setTitle(f"Billing Information - {filename}")
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, y_position, "Billing Information")
    y_position -= 30
    
    # Add each order
    p.setFont("Helvetica", 12)
    for order in orders:
        p.drawString(100, y_position, f"Order #: {order.order_number}")
        y_position -= 20
        p.drawString(120, y_position, f"Date: {order.created_at.strftime('%Y-%m-%d %H:%M')}")
        y_position -= 20
        p.drawString(120, y_position, f"Status: {order.status}")
        y_position -= 20
        p.drawString(120, y_position, f"Total: ${order.total_amount}")
        y_position -= 20
        
        # Add order items
        p.setFont("Helvetica-Bold", 10)
        p.drawString(120, y_position, "Items:")
        y_position -= 15
        p.setFont("Helvetica", 10)
        
        for item in order.items.all():
            # Check if we need to start a new page
            if y_position < 100:
                p.showPage()
                y_position = 750
                p.setFont("Helvetica", 10)
                
            p.drawString(140, y_position, f"{item.product.name} x {item.quantity} @ ${item.price} = ${item.price * item.quantity}")
            y_position -= 15
            
        y_position -= 20
        
        # Check if we need to start a new page for the next order
        if y_position < 200 and order != orders.last():
            p.showPage()
            y_position = 750
            p.setFont("Helvetica", 12)
    
    # Close the PDF object cleanly
    p.showPage()
    p.save()
    
    # FileResponse sets the Content-Disposition header so that browsers
    # present the option to save the file.
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"{filename}.pdf")

def export_orders_csv(orders, filename):
    """Helper function to generate CSV for orders"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Order Number', 'Date', 'Status', 'Total Amount', 'Item Name', 'Quantity', 'Price', 'Subtotal'])
    
    for order in orders:
        for item in order.items.all():
            writer.writerow([
                order.order_number,
                order.created_at.strftime('%Y-%m-%d %H:%M'),
                order.status,
                order.total_amount,
                item.quantity,
                item.price,
                item.price * item.quantity
            ])
    
    return response

@login_required
def email_bill(request, order_id=None):
    """View to send billing information via email"""
    order = get_object_or_404(Order, id=order_id)
    
    # Check permissions
    if request.user.role == 'customer':
        if order.customer != request.user:
            return HttpResponseForbidden("You cannot access this order")
                
    elif request.user.role in ['warehouse_manager', 'staff']:
        # Staff can only email if they're assigned
        if request.user.role == 'staff' and order.assigned_to != request.user:
            return HttpResponseForbidden("You are not assigned to handle this order")
    
    if request.method == "POST":
        recipient_email = request.POST.get('email')
        if not recipient_email:
            recipient_email = order.customer.email
        
        # Generate email content with order details
        email_subject = f"Your Order Invoice #{order.order_number}"
        email_body = f"""
        Dear {order.customer.username},

        Thank you for your order. Here is your billing information:

        Order Number: {order.order_number}
        Date: {order.created_at.strftime('%Y-%m-%d %H:%M')}
        Status: {order.status}
        Total Amount: ${order.total_amount}

        Order Items:
        """
        
        # Add items to email body
        for item in order.items.all():
            email_body += f"\n- {item.product.name} x {item.quantity} @ ${item.price} = ${item.price * item.quantity}"
        
        email_body += f"""

        If you have any questions about your order, please contact our customer service.

        Thank you for shopping with us!
        """
        
        # Send the email
        try:
            send_mail(
                email_subject,
                email_body,
                'your_email@example.com',  # Replace with your system email
                [recipient_email],
                fail_silently=False,
            )
            
            # Log the activity
            ActivityLog.objects.create(
                admin=request.user,
                action=f"Sent invoice for order #{order.order_number} to {recipient_email}"
            )
            
            messages.success(request, f"Invoice has been sent to {recipient_email}")
            
            # Redirect based on user role
            if request.user.role == 'customer':
                return redirect('order_detail', order_id=order.id)
            elif request.user.role == 'staff':
                return redirect('staff_deliveries')
            else:
                return redirect('warehouse_orders')
                
        except Exception as e:
            messages.error(request, f"Error sending email: {str(e)}")
            return redirect('order_detail', order_id=order.id)
    
    # For GET requests, show the email form
    return render(request, 'email_bill.html', {'order': order})

@login_required
def get_notification_count(request):
    """API endpoint to get the count of unread notifications for the current user"""
    try:
        unread_count = request.user.notifications.filter(is_read=False).count()
        return JsonResponse({'count': unread_count})
    except Exception as e:
        print(f"Error getting notification count: {str(e)}")
        return JsonResponse({'count': 0})

@login_required
def staff_inventory_management(request):
    """
    View for staff members to manage inventory products.
    Shows products, allows updating stock levels, and checking low stock items.
    """
    if request.user.role != 'staff':
        return HttpResponseForbidden("You are not authorized to view this page")
    
    # Get search and filter parameters
    search_query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    
    # Start with all products
    products = Product.objects.all().select_related('category', 'warehouse')
    
    # Apply search filter if provided
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Apply category filter if provided
    if category_id:
        try:
            products = products.filter(category_id=int(category_id))
        except (ValueError, TypeError):
            pass  # Invalid category_id, ignore filter
    
    # Get categories for the filter dropdown
    categories = Category.objects.all()
    
    # Identify low stock products
    low_stock_products = get_low_stock_products()
    
    context = {
        'products': products,
        'categories': categories,
        'low_stock_products': low_stock_products,
        'search_query': search_query,
        'selected_category': category_id,
        'total_products': products.count(),
        'low_stock_count': low_stock_products.count()
    }
    
    return render(request, 'staff_inventory.html', context)

@login_required
def staff_customer_management(request):
    """
    View for staff members to manage customer information and orders.
    Shows customer list, allows searching, and viewing customer orders.
    """
    if request.user.role != 'staff':
        return HttpResponseForbidden("You are not authorized to view this page")
    
    # Get customers (all users with role='customer')
    customers = CustomUser.objects.filter(role='customer').order_by('username')
    
    # Get search parameter
    search_query = request.GET.get('q', '')
    
    # Apply search filter if provided
    if search_query:
        customers = customers.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # Get customer orders if a customer_id is provided
    customer_id = request.GET.get('customer_id')
    customer_orders = None
    selected_customer = None
    
    if customer_id:
        try:
            selected_customer = CustomUser.objects.get(id=customer_id, role='customer')
            customer_orders = Order.objects.filter(customer=selected_customer).order_by('-created_at')
        except CustomUser.DoesNotExist:
            messages.error(request, "Selected customer does not exist")
    
    context = {
        'customers': customers,
        'search_query': search_query,
        'total_customers': customers.count(),
        'customer_orders': customer_orders,
        'selected_customer': selected_customer
    }
    
    return render(request, 'staff_customers.html', context)

@login_required
def staff_update_stock(request, product_id):
    """
    View for staff members to update product's stock levels.
    """
    if request.user.role != 'staff':
        return HttpResponseForbidden("You are not authorized to perform this action")
    
    if request.method == 'POST':
        try:
            product = get_object_or_404(Product, id=product_id)
            stock_change = int(request.POST.get('stock_change'))
            
            # Update the stock
            product.stock += stock_change
            
            # Ensure stock doesn't go below zero
            if product.stock < 0:
                product.stock = 0
                
            product.save()
            
            # Log the activity
            ActivityLog.objects.create(
                admin=request.user,
                action=f"Staff updated stock for {product.name} by {stock_change} units (New stock: {product.stock})"
            )
            messages.success(request, f"Stock updated successfully for {product.name}")
        except Exception as e:
            messages.error(request, f"Error updating stock: {str(e)}")
    
    return redirect('staff_inventory_management')

@login_required
def order_dashboard(request):
    """View for order management dashboard"""
    if request.user.role not in ['admin', 'warehouse_manager', 'super_admin']:
        return HttpResponseForbidden("You are not authorized to view this page")
    
    # Get all orders with their status
    all_orders = Order.objects.all().select_related('customer')
    
    # Get status filter from query params
    status_filter = request.GET.get('status', '')
    
    # Apply status filter if provided
    filtered_orders = all_orders
    if status_filter and status_filter != 'all':
        filtered_orders = all_orders.filter(status=status_filter)
    
    # Order by most recent first
    filtered_orders = filtered_orders.order_by('-created_at')
    
    # Calculate order statistics
    context = {
        'recent_orders': filtered_orders[:10],  # Show 10 most recent orders
        'total_orders': all_orders.count(),
        'pending_orders': all_orders.filter(status='pending').count(),
        'processing_orders': all_orders.filter(status='processing').count(),
        'shipped_orders': all_orders.filter(status='shipped').count(),
        'delivered_orders': all_orders.filter(status='delivered').count(),
        'cancelled_orders': all_orders.filter(status='cancelled').count(),
        'current_status': status_filter or 'all'
    }
    
    return render(request, 'order_dashboard.html', context)