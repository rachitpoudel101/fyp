from django.utils import timezone  #  timezone import
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.contrib.auth.decorators import login_required
from Inventory.models import Order, OrderItem, Product, Category
from Inventory.forms import CategoryForm, ProductForm, OrderForm
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
    
    context = {
        'warehouse_managers': warehouse_managers,
        'staff_members': staff_members,
        'warehouses': warehouses,
        'available_managers': available_managers,
        'low_stock_products': low_stock_products,
        'user_form': CustomUserCreationForm(),
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
        is_active=True
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
    
    # Get count of orders by status
    pending_count = Order.objects.filter(id__in=order_ids, status='pending').count()
    processing_count = Order.objects.filter(id__in=order_ids, status='processing').count()
    shipped_count = Order.objects.filter(id__in=order_ids, status='shipped').count()
    delivered_count = Order.objects.filter(id__in=order_ids, status='delivered').count()
    
    # Get unread notifications if the table exists
    try:
        unread_notifications = request.user.notifications.filter(is_read=False)[:5]
        notification_count = unread_notifications.count()
    except Exception:
        # Handle the case when notifications aren't available
        unread_notifications = []
        notification_count = 0
    
    context = {
        'warehouse': warehouse,
        'recent_orders': recent_orders,
        'pending_count': pending_count,
        'processing_count': processing_count,
        'shipped_count': shipped_count,
        'delivered_count': delivered_count,
        'total_orders': len(order_ids),
        'unread_notifications': unread_notifications,
        'notification_count': notification_count
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
    
    # Apply status filter if provided
    orders = Order.objects.filter(id__in=order_ids)
    if status_filter and status_filter != 'all':
        orders = orders.filter(status=status_filter)
    
    # Order by most recent first
    orders = orders.order_by('-created_at')
    
    context = {
        'warehouse': warehouse,
        'orders': orders,
        'current_status': status_filter or 'all'
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
        return HttpResponseForbidden("You are not authorized to view this page")
    
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
    
    # Get ALL warehouse managers and staff members regardless of created_by field
    warehouse_managers = CustomUser.objects.filter(role='warehouse_manager')
    staff_members = CustomUser.objects.filter(role='staff', created_by=request.user)
    
    context = {
        'users': users,
        'warehouse_managers': warehouse_managers,
        'staff_members': staff_members,
    }
    return render(request, 'user_statistics.html', context)

@login_required
def product_management(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden("You are not authorized to view this page")
    
    if request.method == "POST":
        # Handle product deletion
        if 'delete_product_id' in request.POST:
            product_id = request.POST.get('delete_product_id')
            try:
                product = Product.objects.get(id=product_id)
                product_name = product.name
                product.delete()
                messages.success(request, f"Product '{product_name}' was deleted successfully!")
                return redirect('product_management')
            except Product.DoesNotExist:
                messages.error(request, "Product not found.")
                return redirect('product_management')
            except Exception as e:
                messages.error(request, f"Error deleting product: {str(e)}")
                return redirect('product_management')
        
        # Handle product update - FIXED VERSION
        elif 'edit_product_id' in request.POST:
            product_id = request.POST.get('edit_product_id')
            try:
                print(f"DEBUG: Updating product ID: {product_id}")
                product = Product.objects.get(id=product_id)
                # Get form fields with validation
                product.name = request.POST.get('edit_name', '').strip()
                if not product.name:
                    raise ValueError("Product name cannot be empty")
                    
                price = request.POST.get('edit_price', '')
                if price:
                    product.price = float(price)
                
                stock = request.POST.get('edit_stock', '')
                if stock:
                    product.stock = int(stock)
                
                product.description = request.POST.get('edit_description', '').strip()
                
                # Handle category
                category_id = request.POST.get('edit_category')
                if category_id:
                    try:
                        category = Category.objects.get(id=category_id)
                        product.category = category
                        
                        # Set expires based on category setting
                        if category.expires:
                            expires_date = request.POST.get('edit_expires')
                            if (expires_date and expires_date.strip()):
                                product.expires = expires_date
                            else:
                                # If category requires expiry but no date provided, handle error
                                raise ValueError("Expiry date is required for this category")
                        else:
                            product.expires = None
                            
                    except Category.DoesNotExist:
                        print(f"DEBUG: Category with ID {category_id} doesn't exist")
                
                # Get warehouse ID from form
                warehouse_id = request.POST.get('edit_warehouse')
                if warehouse_id:
                    try:
                        warehouse = Warehouse.objects.get(id=warehouse_id)
                        
                        # Check if warehouse can handle expiring products if needed
                        if product.expires and not warehouse.handles_expiring:
                            messages.warning(request, f"Warning: Selected warehouse does not handle expiring products. Product has been assigned, but please consider a different warehouse.")
                        
                        product.warehouse = warehouse
                    except Warehouse.DoesNotExist:
                        messages.error(request, f"Selected warehouse does not exist.")
                        return redirect('product_management')
                
                product.save()
                
                # Log this action
                ActivityLog.objects.create(
                    admin=request.user,
                    action=f"Updated product {product.name} (ID: {product_id})"
                )
                
                messages.success(request, f"Product '{product.name}' was updated successfully!")
                return redirect('product_management')
                
            except Product.DoesNotExist:
                messages.error(request, "Product not found.")
                return redirect('product_management')
            except ValueError as e:
                messages.error(request, str(e))
                return redirect('product_management')
            except Exception as e:
                print(f"DEBUG: Error updating product: {str(e)}")
                messages.error(request, f"Error updating product: {str(e)}")
                return redirect('product_management')
        
        # Handle product creation (existing code)
        else:
            product_id = request.POST.get('product_id')
            if product_id:
                product = get_object_or_404(Product, id=product_id)
                form = ProductForm(request.POST, request.FILES, instance=product)
            else:
                form = ProductForm(request.POST, request.FILES)
            
            if form.is_valid():
                try:
                    product = form.save(commit=False)
                    # Check if category requires expiry date
                    if product.category and product.category.expires:
                        if not product.expires:
                            return JsonResponse({
                                'success': False,
                                'error': 'This category requires an expiry date',
                                'message': 'Please set an expiry date for this product'
                            })
                    
                    # Get warehouse from form if provided
                    warehouse_id = request.POST.get('warehouse')
                    if warehouse_id:
                        try:
                            warehouse = Warehouse.objects.get(id=warehouse_id)
                            
                            # Check if warehouse can handle expiring products if needed
                            if product.expires and not warehouse.handles_expiring:
                                return JsonResponse({
                                    'success': False,
                                    'error': 'Selected warehouse cannot handle expiring products',
                                    'message': 'Please select a warehouse that handles expiring products'
                                })
                                
                            product.warehouse = warehouse
                        except Warehouse.DoesNotExist:
                            return JsonResponse({
                                'success': False,
                                'error': 'Selected warehouse does not exist',
                                'message': 'Please select a valid warehouse'
                            })
                    else:
                        # Fallback to original logic if no warehouse selected
                        if product.category and product.category.expires:
                            # Find expiring warehouse
                            warehouse = Warehouse.objects.filter(handles_expiring=True).first()
                            if not warehouse:
                                warehouse = Warehouse.objects.create(
                                    name="Expiring Products Warehouse",
                                    location="Default Location",
                                    handles_expiring=True
                                )
                        else:
                            # If category doesn't expire or no category, clear expiry date
                            product.expires = None
                            # Find non-expiring warehouse
                            warehouse = Warehouse.objects.filter(handles_expiring=False).first()
                            if not warehouse:
                                warehouse = Warehouse.objects.create(
                                    name="Non-Expiring Products Warehouse",
                                    location="Default Location",
                                    handles_expiring=False
                                )
                        
                        product.warehouse = warehouse
                    
                    product.save()
                    
                    ActivityLog.objects.create(
                        admin=request.user,
                        action=f"{'Updated' if product_id else 'Added'} product {product.name}"
                    )
                    
                    return JsonResponse({
                        'success': True,
                        'message': f"Product successfully {'updated' if product_id else 'added'}!"
                    })
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    })
            else:
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = error_list[0]
                
                return JsonResponse({
                    'success': False,
                    'error': errors,
                    'message': 'Please fill in all required fields correctly.'
                })
    
    products = Product.objects.all().select_related('warehouse')
    categories = Category.objects.all()
    warehouses = Warehouse.objects.all()
    
    context = {
        'products': products,
        'categories': categories,
        'warehouses': warehouses,
        'form': ProductForm()
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
    # Debug information
    print(f"ADD CATEGORY VIEW ACCESSED: user={request.user.username}, role={request.user.role}")
    print(f"REQUEST METHOD: {request.method}")
    
    if request.user.role != 'admin':
        print(f"UNAUTHORIZED: User {request.user.username} with role {request.user.role} attempted to add category")
        return JsonResponse({
            'success': False,
            'error': 'Only admin users can add categories'
        }, status=403)
    
    if request.method != "POST":
        return JsonResponse({
            'success': False,
            'error': 'Only POST method is allowed'
        }, status=405)
    
    try:
        # Print POST data for debugging
        print("POST DATA:", request.POST)
        
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
        
        # Case-insensitive check for existing category
        if Category.objects.filter(name__iexact(name).exists()):
            print(f"ERROR: Category '{name}' already exists")
            return JsonResponse({
                'success': False,
                'error': f'Category "{name}" already exists'
            }, status=400)
        
        # Create new category with expires field
        category = Category.objects.create(
            name=name,
            description=description if description else None,
            expires=expires
        )
        
        print(f"CATEGORY CREATED: ID={category.id}, Name='{category.name}', Expires={category.expires}")
        
        # Log the activity
        ActivityLog.objects.create(
            admin=request.user,
            action=f"Added new category: {category.name} (Expires: {expires})"
        )

        return JsonResponse({
            'success': True,
            'category': {
                'id': category.id,
                'name': category.name,
                'description': category.description or '',
                'expires': category.expires
            },
            'message': f'Category "{category.name}" added successfully!'
        })
        
    except Exception as e:
        print(f"ERROR ADDING CATEGORY: {str(e)}")
        import traceback
        traceback.print_exc()  # This will print the full stack trace
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

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
            'description': product.description or '',
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

@login_required
def super_admin_dashboard(request):
    if request.user.role != 'super_admin':
        return HttpResponseForbidden("You are not authorized to view this page")
    
    admins = CustomUser.objects.filter(role='admin')
    verified_admins = CustomUser.objects.filter(role='admin', is_verified=True)  # Only verified admins
    activities = Order.objects.all()  # Example: Fetch all orders as activities
    pending_admins = CustomUser.objects.filter(role='admin', is_approved=False)
    approved_admins = CustomUser.objects.filter(role='admin', is_approved=True, is_verified=False)
    verification_requests = CustomUser.objects.filter(role='admin', is_approved=False, is_verified=False)
    recent_activities = ActivityLog.objects.order_by('-timestamp')[:10]  # Fetch recent activities

    context = {
        'admins': admins,
        'verified_admins': verified_admins,  # Pass verified admins
        'pending_admins': pending_admins,
        'activities': activities,
        'approved_admins': approved_admins,
        'user_form': CustomUserCreationForm(),  # Form to add new admins
        'verification_requests': verification_requests,
        'recent_activities': recent_activities,  # Pass recent activities
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
                
                # Debug with more details
                print(f"DEBUG: About to save admin - username={user.username}, email={user.email}, role={user.role}")
                
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
                    Super Admin
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
                user.created_by = request.user  # Set the creator
                user.is_email_verified = False
                user.tags = request.POST.getlist('tags')  # Get tags as list
                user.save()
                
                # Generate verification token
                token = generate_verification_token()
                user.verification_token = token
                user.save()
                
                # Send verification email
                resend_verification_email(user, token)
                
                messages.success(request, 'Staff member added successfully. Please check your email to verify your account.')
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
                user.created_by = request.user  # Set the creator
                user.is_email_verified = False
                user.tags = request.POST.getlist('tags')  # Get tags as list
                user.save()
                
                # Generate verification token
                token = generate_verification_token()
                user.verification_token = token
                user.save()
                
                # Send verification email
                resend_verification_email(user, token)
                
                messages.success(request, 'Warehouse manager added successfully. Please check your email to verify your account.')
                return redirect('admin_dashboard')
            except Exception as e:
                messages.error(request, f'Error adding warehouse manager: {str(e)}')
    else:
        form = WarehouseForm()
    
    return render(request, 'add_warehouse_manager.html', {'form': form})

@login_required
def approve_admin(request, admin_id):
    if request.method == "POST":
        admin = get_object_or_404(CustomUser, id=admin_id, role='admin')
        admin.is_approved = True
        admin.save()
        return redirect('super_admin_dashboard')

@login_required
def verify_admin(request, admin_id):
    if request.method == "POST":
        admin = get_object_or_404(CustomUser, id=admin_id, role='admin')
        if admin.is_approved:  # Only allow verification if approved
            admin.is_verified = True
            admin.save()
        return redirect('super_admin_dashboard')

@login_required
def request_verification(request):
    if request.user.role == 'admin' and not request.user.is_verified:
        request.user.is_approved = False  # Reset approval status
        request.user.save()
        messages.success(request, "Your verification request has been sent to the super admin.")
    return redirect('profile')

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
            if manager_id:
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
    
    return HttpResponseBadRequest("Invalid request method")

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

# Add a new dedicated view for product deletion
@login_required
def delete_product(request, product_id):
    # Detailed debug logging
    print(f"DELETE PRODUCT VIEW ACCESSED: product_id={product_id}, user={request.user.username}, role={request.user.role}")
    
    if request.user.role != 'admin':
        print(f"UNAUTHORIZED: User {request.user.username} with role {request.user.role} attempted to delete product {product_id}")
        messages.error(request, "You are not authorized to delete products")
        return redirect('product_management')
    
    try:
        # Get the product
        product = Product.objects.get(id=product_id)
        product_name = product.name
        print(f"FOUND PRODUCT: {product_name} (ID: {product_id})")
        
        # Delete the product
        product.delete()
        print(f"PRODUCT DELETED: {product_name} (ID: {product_id})")
        
        # Log the activity
        ActivityLog.objects.create(
            admin=request.user,
            action=f"Deleted product: {product_name} (ID: {product_id})"
        )
        
        # Set success message
        messages.success(request, f"Product '{product_name}' deleted successfully!")
        
        # For AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"success": True, "message": f"Product '{product_name}' deleted successfully"})
        
        # For regular form submissions
        return redirect('product_management')
    except Product.DoesNotExist:
        print(f"PRODUCT NOT FOUND: ID {product_id}")
        messages.error(request, "Product not found")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"error": "Product not found"}, status=404)
        
        return redirect('product_management')
    except Exception as e:
        print(f"ERROR DELETING PRODUCT {product_id}: {str(e)}")
        messages.error(request, f"Failed to delete product: {str(e)}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"error": f"Failed to delete product: {str(e)}"}, status=500)
        
        return redirect('product_management')

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
    
    if request.method == 'POST':
        warehouse_name = warehouse.name
        try:
            # Check if products are associated with this warehouse
            associated_products = Product.objects.filter(warehouse=warehouse)
            product_count = associated_products.count()
            
            # If products exist, reassign them to a default warehouse before deletion
            if product_count > 0:
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
                    f"{product_count} products from warehouse '{warehouse_name}' have been reassigned to '{default_warehouse.name}'."
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
def edit_category(request, category_id):
    """View function to edit a category"""
    if request.user.role != 'admin':
        return HttpResponseForbidden("You are not authorized to perform this action")
    
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            # Get the expires field value
            expires = request.POST.get('expires') == 'on'
            
            if not name:
                messages.error(request, "Category name cannot be empty")
                return redirect('product_management')
            
            # Check if another category with this name exists (excluding current category)
            if Category.objects.filter(name__iexact=name).exclude(id=category_id).exists():
                messages.error(request, f'Category "{name}" already exists')
                return redirect('product_management')
            
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
            return redirect('product_management')
            
        except Exception as e:
            messages.error(request, f'Error updating category: {str(e)}')
            return redirect('product_management')
    return redirect('product_management')

@login_required
def delete_category(request, category_id):
    """View function to delete a category"""
    if request.user.role != 'admin':
        return HttpResponseForbidden("You are not authorized to perform this action")
    
    category = get_object_or_404(Category, id=category_id)
    category_name = category.name
    
    if request.method == 'POST':
        try:
            # Check if products are associated with this category
            if Product.objects.filter(category=category).exists():
                messages.error(request, f'Cannot delete category "{category_name}" because it has products associated with it.')
                return redirect('product_management')
                
            category.delete()
            
            # Log the activity
            ActivityLog.objects.create(
                admin=request.user,
                action=f"Deleted category: {category_name}"
            )
            messages.success(request, f'Category "{category_name}" deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting category: {str(e)}')
        return redirect('product_management')
    return redirect('product_management')

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
        
        # Check if there's enough stock
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
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        
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
                # Create order
                order = Order.objects.create(
                    order_number=str(uuid.uuid4()),
                    customer=request.user,
                    total_amount=total_amount,
                    status='pending',
                    # Add shipping details from form
                    shipping_address=request.POST.get('shipping_address'),
                    shipping_city=request.POST.get('shipping_city'),
                    shipping_state=request.POST.get('shipping_state'),
                    shipping_country=request.POST.get('shipping_country'),
                    shipping_zip=request.POST.get('shipping_zip')
                )
                
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
                
                # Log the activity
                ActivityLog.objects.create(
                    admin=None,  # No admin for customer actions
                    user=request.user,
                    action=f"Placed order #{order.order_number} for ${order.total_amount}"
                )
                
                messages.success(request, "Your order has been placed successfully!")
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
            stock_change = int(request.POST.get('stock_change', 0))
            
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
    
    return redirect('warehouse_dashboard')