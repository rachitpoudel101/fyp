from time import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.contrib.auth.decorators import login_required
from Inventory.models import Order, OrderItem, Product, Category
from Inventory.forms import CategoryForm, ProductForm, OrderForm
from .forms import CustomUserCreationForm, WarehouseForm, StaffCreationForm
from .models import CustomUser, Warehouse, ActivityLog  # Add ActivityLog to the importser, Warehouse
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.urls import reverse
import uuid
from django.db.models import Sum, Q, F
from django.contrib import messages  # Import for user notifications

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
        return redirect('order_list')
    else:
        return HttpResponseForbidden("You do not have permission to view this page.")

# ...existing code...

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
    
    # Get all users with their creators (admins)
    users = CustomUser.objects.select_related('created_by').all().order_by('role')
    
    # Filter users based on role and created_by
    warehouse_managers = CustomUser.objects.filter(role='warehouse_manager')
    staff_members = CustomUser.objects.filter(role='staff')
    
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
                        product.category = Category.objects.get(id=category_id)
                    except Category.DoesNotExist:
                        print(f"DEBUG: Category with ID {category_id} doesn't exist")
                
                # Handle expiry date
                expires_date = request.POST.get('edit_expires')
                if expires_date and expires_date.strip():
                    product.expires = expires_date
                else:
                    product.expires = None
                
                # Find appropriate warehouse based on expiry
                if product.expires:
                    warehouse = Warehouse.objects.filter(handles_expiring=True).first()
                    if not warehouse:
                        warehouse = Warehouse.objects.create(
                            name="Expiring Products Warehouse",
                            location="Default Location",
                            handles_expiring=True
                        )
                else:
                    warehouse = Warehouse.objects.filter(handles_expiring=False).first()
                    if not warehouse:
                        warehouse = Warehouse.objects.create(
                            name="Non-Expiring Products Warehouse",
                            location="Default Location",
                            handles_expiring=False
                        )
                
                product.warehouse = warehouse
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
                    
                    # Find appropriate warehouse based on expiry
                    if product.expires:
                        warehouse = Warehouse.objects.filter(handles_expiring=True).first()
                        if not warehouse:
                            warehouse = Warehouse.objects.create(
                                name="Expiring Products Warehouse",
                                location="Default Location",
                                handles_expiring=True
                            )
                    else:
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
    if request.user.role != 'admin':
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
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not name:
            return JsonResponse({
                'success': False,
                'error': 'Category name cannot be empty'
            }, status=400)

        # Case-insensitive check for existing category
        if Category.objects.filter(name__iexact(name)).exists():
            return JsonResponse({
                'success': False,
                'error': f'Category "{name}" already exists'
            }, status=400)

        # Create new category
        category = Category.objects.create(
            name=name,
            description=description if description else None
        )
        
        # Log the activity
        ActivityLog.objects.create(
            admin=request.user,
            action=f"Added new category: {category.name}"
        )

        return JsonResponse({
            'success': True,
            'category': {
                'id': category.id,
                'name': category.name,
                'description': category.description or ''
            },
            'message': f'Category "{category.name}" added successfully!'
        })

    except Exception as e:
        print(f"Error adding category: {str(e)}")
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
        'activities': activities,
        'user_form': CustomUserCreationForm(),  # Form to add new admins
        'pending_admins': pending_admins,
        'approved_admins': approved_admins,
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
                
                # Generate verification token
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
                send_verification_email(user, token)
                
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
                send_verification_email(user, token)
                
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
    return redirect('profile')  # Redirect to the profile page

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

@login_required
def profile_view(request):
    return render(request, 'profile.html', {
        'user': request.user
    })

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
                'your_email@example.com',
                [user.email],
            )
            messages.success(request, 'Password reset link has been sent to your email.')
            return redirect('login')
        except CustomUser.DoesNotExist:
            messages.error(request, 'No user found with this email address.')
    return render(request, 'forgot_password.html')

def reset_password(request, token):
    try:
        user = CustomUser.objects.get(
            reset_password_token=token,
            reset_password_expires__gt=timezone.now()
        )
        if request.method == 'POST':
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            
            if password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'reset_password.html')
            
            user.set_password(password)
            user.reset_password_token = None
            user.reset_password_expires = None
            user.save()
            
            messages.success(request, 'Your password has been reset successfully. You can now login.')
            return redirect('login')
            
        return render(request, 'reset_password.html')
        
    except CustomUser.DoesNotExist:
        messages.error(request, 'Invalid or expired reset link.')
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