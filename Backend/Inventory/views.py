from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from user.models import Cart, Wishlist
from .models import Order, OrderItem, Product, Category
from .forms import OrderForm, OrderItemForm, ProductForm, CategoryForm

@login_required
def create_order(request):
    if request.user.role != 'customer':
        return HttpResponseForbidden("You are not authorized to view this page")
    
    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.customer = request.user
            order.save()
            return redirect('order_detail', order_id=order.id)
    else:
        form = OrderForm()
    return render(request, 'create_order.html', {'form': form})

@login_required
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == "POST":
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            return redirect('order_detail', order_id=order.id)
    else:
        form = OrderForm(instance=order)
    return render(request, 'update_order_status.html', {'form': form, 'order': order})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # Allow customer who placed the order to view it
    if request.user.role == 'customer' and order.customer == request.user:
        return render(request, 'order_detail.html', {'order': order})
    
    # Allow warehouse manager to view if order contains products from their warehouse
    elif request.user.role == 'warehouse_manager' and request.user.managed_warehouse:
        # Check if any order item's product belongs to this manager's warehouse
        order_items = OrderItem.objects.filter(order=order, product__warehouse=request.user.managed_warehouse)
        if order_items.exists():
            return render(request, 'order_detail.html', {'order': order, 'warehouse_items': order_items})
    
    # For admins and superadmins
    elif request.user.role in ['admin', 'super_admin']:
        return render(request, 'order_detail.html', {'order': order})
        
    return HttpResponseForbidden("You are not authorized to view this page")

@login_required
def order_list(request):
    if request.user.role == 'customer':
        # ...existing customer order list code...
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
    
    elif request.user.role == 'warehouse_manager' and request.user.managed_warehouse:
        # Get orders containing products from this manager's warehouse
        managed_warehouse = request.user.managed_warehouse
        
        # Find order IDs that contain products from this warehouse
        order_ids = OrderItem.objects.filter(
            product__warehouse=managed_warehouse
        ).values_list('order_id', flat=True).distinct()
        
        # Get those orders
        orders = Order.objects.filter(id__in=order_ids).order_by('-created_at')
        
        return render(request, 'warehouse_orders.html', {
            'orders': orders,
            'warehouse': managed_warehouse
        })
    
    elif request.user.role in ['admin', 'super_admin']:
        orders = Order.objects.all()
        return render(request, 'order_list.html', {'orders': orders})
    
    else:
        return HttpResponseForbidden("You are not authorized to view this page")

@login_required
def products(request):
    """View all products for admin"""
    if request.user.role not in ['admin']:
        return HttpResponseForbidden("You are not authorized to view this page")
    
    products = Product.objects.all()
    return render(request, 'products.html', {'products': products})

@login_required
def add_product(request):
    """Add a new product"""
    if request.user.role not in ['admin']:
        return HttpResponseForbidden("You are not authorized to view this page")
    
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('products')  # Changed from admin_products to products
    else:
        form = ProductForm()
    
    return render(request, 'add_product.html', {'form': form})

@login_required
def update_product(request, product_id):
    """Update an existing product"""
    if request.user.role not in ['admin']:
        return HttpResponseForbidden("You are not authorized to view this page")
    
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('products')  # Changed from admin_products to products
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'update_product.html', {'form': form, 'product': product})

@login_required
def delete_product(request, product_id):
    """Delete a product"""
    if request.user.role not in ['admin']:
        return HttpResponseForbidden("You are not authorized to view this page")
    
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == "POST":
        product.delete()
        return redirect('products')  # Changed from admin_products to products
    
    return render(request, 'delete_product.html', {'product': product})

@login_required
def categories(request):
    """View all categories for admin"""
    if request.user.role not in ['admin']:
        return HttpResponseForbidden("You are not authorized to view this page")
    
    categories = Category.objects.all()
    return render(request, 'categories.html', {'categories': categories})

@login_required
def add_category(request):
    """Add a new category"""
    if request.user.role not in ['admin']:
        return HttpResponseForbidden("You are not authorized to view this page")
    
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('categories')  # Changed from admin_categories to categories
    else:
        form = CategoryForm()
    
    return render(request, 'add_category.html', {'form': form})

@login_required
def update_category(request, category_id):
    """Update an existing category"""
    if request.user.role not in ['admin']:
        return HttpResponseForbidden("You are not authorized to view this page")
    
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('categories')  # Changed from admin_categories to categories
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'update_category.html', {'form': form, 'category': category})

@login_required
def delete_category(request, category_id):
    """Delete a category"""
    if request.user.role not in ['admin']:
        return HttpResponseForbidden("You are not authorized to view this page")
    
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == "POST":
        category.delete()
        return redirect('categories')  # Changed from admin_categories to categories
    
    return render(request, 'delete_category.html', {'category': category})
