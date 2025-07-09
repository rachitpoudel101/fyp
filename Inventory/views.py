from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from user.models import Cart, Wishlist
from .models import Order, OrderItem, Product, Category
from .forms import OrderForm, ProductForm, CategoryForm
import io
import xlsxwriter
from django.http import HttpResponse


@login_required
def create_order(request):
    if request.user.role != "customer":
        return HttpResponseForbidden("You are not authorized to view this page")

    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.customer = request.user
            order.save()
            return redirect("order_detail", order_id=order.id)
    else:
        form = OrderForm()
    return render(request, "create_order.html", {"form": form})


@login_required
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == "POST":
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            return redirect("order_detail", order_id=order.id)
    else:
        form = OrderForm(instance=order)
    return render(request, "update_order_status.html", {"form": form, "order": order})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # Allow customer who placed the order to view it
    if request.user.role == "customer" and order.customer == request.user:
        return render(request, "order_detail.html", {"order": order})

    # Allow warehouse manager to view if order contains products from their warehouse
    elif request.user.role == "warehouse_manager" and request.user.managed_warehouse:
        # Check if any order item's product belongs to this manager's warehouse
        order_items = OrderItem.objects.filter(
            order=order, product__warehouse=request.user.managed_warehouse
        )
        if order_items.exists():
            return render(
                request,
                "order_detail.html",
                {"order": order, "warehouse_items": order_items},
            )

    # For admins and superadmins
    elif request.user.role in ["admin", "super_admin"]:
        return render(request, "order_detail.html", {"order": order})

    return HttpResponseForbidden("You are not authorized to view this page")


@login_required
def order_list(request):
    if request.user.role == "customer":
        # ...existing customer order list code...
        orders = Order.objects.filter(customer=request.user)
        products = Product.objects.all()

        # Get or create cart and wishlist for displaying counts
        cart, _ = Cart.objects.get_or_create(user=request.user)
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)

        context = {
            "orders": orders,
            "products": products,
            "cart": cart,
            "wishlist": wishlist,
        }

        return render(request, "order_list.html", context)

    elif request.user.role == "warehouse_manager" and request.user.managed_warehouse:
        # Get orders containing products from this manager's warehouse
        managed_warehouse = request.user.managed_warehouse

        # Find order IDs that contain products from this warehouse
        order_ids = (
            OrderItem.objects.filter(product__warehouse=managed_warehouse)
            .values_list("order_id", flat=True)
            .distinct()
        )

        # Get those orders
        orders = Order.objects.filter(id__in=order_ids).order_by("-created_at")

        return render(
            request,
            "warehouse_orders.html",
            {"orders": orders, "warehouse": managed_warehouse},
        )

    elif request.user.role in ["admin", "super_admin"]:
        orders = Order.objects.all()
        return render(request, "order_list.html", {"orders": orders})

    else:
        return HttpResponseForbidden("You are not authorized to view this page")


@login_required
def products(request):
    """View all products for admin"""
    if request.user.role not in ["admin"]:
        return HttpResponseForbidden("You are not authorized to view this page")

    from django.utils import timezone
    from django.db.models import Q

    now = timezone.now()

    # Separate expired and non-expired products
    expired_products = Product.objects.filter(
        expires__isnull=False, expires__lt=now
    ).order_by("expires")

    non_expired_products = Product.objects.filter(
        Q(expires__isnull=True) | Q(expires__gte=now)
    ).order_by("-created_at")

    context = {
        "expired_products": expired_products,
        "non_expired_products": non_expired_products,
        "total_products": Product.objects.count(),
        "expired_count": expired_products.count(),
        "non_expired_count": non_expired_products.count(),
    }

    return render(request, "products.html", context)


@login_required
def add_product(request):
    """Add a new product"""
    if request.user.role not in ["admin"]:
        return HttpResponseForbidden("You are not authorized to view this page")

    # Check if there are any categories available
    if not Category.objects.exists():
        from django.contrib import messages

        messages.warning(
            request, "You need to create at least one category before adding products."
        )
        return redirect("add_category")

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            from django.contrib import messages

            messages.success(request, "Product added successfully!")
            return redirect("products")  # Changed from admin_products to products
    else:
        form = ProductForm()

    return render(request, "add_product.html", {"form": form})


@login_required
def update_product(request, product_id):
    """Update an existing product"""
    if request.user.role not in ["admin"]:
        return HttpResponseForbidden("You are not authorized to view this page")

    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect("products")  # Changed from admin_products to products
    else:
        form = ProductForm(instance=product)

    return render(request, "update_product.html", {"form": form, "product": product})


@login_required
def delete_product(request, product_id):
    """Delete a product"""
    if request.user.role not in ["admin"]:
        return HttpResponseForbidden("You are not authorized to view this page")

    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        product.delete()
        return redirect("products")  # Changed from admin_products to products

    return render(request, "delete_product.html", {"product": product})


@login_required
def categories(request):
    """View all categories for admin"""
    if request.user.role not in ["admin"]:
        return HttpResponseForbidden("You are not authorized to view this page")

    categories = Category.objects.all()
    return render(request, "categories.html", {"categories": categories})


@login_required
def add_category(request):
    """Add a new category"""
    if request.user.role not in ["admin"]:
        return HttpResponseForbidden("You are not authorized to view this page")

    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("categories")  # Changed from admin_categories to categories
    else:
        form = CategoryForm()

    return render(request, "add_category.html", {"form": form})


@login_required
def update_category(request, category_id):
    """Update an existing category"""
    if request.user.role not in ["admin"]:
        return HttpResponseForbidden("You are not authorized to view this page")

    category = get_object_or_404(Category, id=category_id)

    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect("categories")  # Changed from admin_categories to categories
    else:
        form = CategoryForm(instance=category)

    return render(request, "update_category.html", {"form": form, "category": category})


@login_required
def delete_category(request, category_id):
    """Delete a category"""
    if request.user.role not in ["admin"]:
        return HttpResponseForbidden("You are not authorized to view this page")

    category = get_object_or_404(Category, id=category_id)

    if request.method == "POST":
        category.delete()
        return redirect("categories")  # Changed from admin_categories to categories

    return render(request, "delete_category.html", {"category": category})


def download_receipt(request, order_id):
    """Generate and download an Excel receipt for an order"""
    try:
        # Get the order with all related data
        order = Order.objects.get(id=order_id)

        # Security check - only allow staff or the order owner to download
        if not (request.user.is_staff or request.user == order.customer):
            return HttpResponse("Permission denied", status=403)

        # Create an in-memory output file
        output = io.BytesIO()

        try:
            # Create a workbook with more explicit options
            workbook = xlsxwriter.Workbook(
                output, {"in_memory": True, "constant_memory": False}
            )
            worksheet = workbook.add_worksheet("Receipt")

            # Add formats
            bold = workbook.add_format({"bold": True})
            title = workbook.add_format({"bold": True, "font_size": 14})
            header = workbook.add_format(
                {"bold": True, "bg_color": "#f0f0f0", "border": 1}
            )
            cell_format = workbook.add_format({"border": 1})
            money_format = workbook.add_format({"border": 1, "num_format": "$#,##0.00"})
            workbook.add_format({"num_format": "yyyy-mm-dd hh:mm"})

            # Write receipt header
            worksheet.merge_range("A1:E1", "ORDER RECEIPT", title)
            worksheet.write("A3", "Order Number:", bold)
            worksheet.write("B3", str(order.order_number))  # Ensure string
            worksheet.write("A4", "Date:", bold)
            worksheet.write("B4", order.created_at.strftime("%Y-%m-%d %H:%M"))
            worksheet.write("A5", "Customer:", bold)
            customer_name = (
                order.customer.get_full_name() if order.customer else "Guest"
            )
            worksheet.write("B5", str(customer_name))  # Ensure string
            worksheet.write("A6", "Status:", bold)
            worksheet.write("B6", str(order.status).title())  # Ensure string

            # Write item headers
            row = 8
            worksheet.write(row, 0, "Product", header)
            worksheet.write(row, 1, "Quantity", header)
            worksheet.write(row, 2, "Price", header)
            worksheet.write(row, 3, "Total", header)
            row += 1

            # Write items - safely get items
            if hasattr(order, "orderitem_set"):
                items = order.orderitem_set.all()
            elif hasattr(order, "items"):
                items = order.items.all()
            else:
                items = OrderItem.objects.filter(order=order)

            # Handle case of no items
            if not items:
                worksheet.write(row, 0, "No items in this order", cell_format)
                worksheet.write(row, 1, 0, cell_format)
                worksheet.write(row, 2, 0, money_format)
                worksheet.write(row, 3, 0, money_format)
                row += 1
            else:
                for item in items:
                    # Safely get product name
                    product_name = "Unknown Product"
                    if hasattr(item, "product") and item.product:
                        product_name = item.product.name

                    worksheet.write(row, 0, str(product_name), cell_format)

                    # Ensure quantity is a number
                    quantity = int(item.quantity) if hasattr(item, "quantity") else 0
                    worksheet.write(row, 1, quantity, cell_format)

                    # Safely get the price as a float
                    price = 0.0
                    if hasattr(item, "price"):
                        try:
                            price = float(item.price) if item.price is not None else 0.0
                        except (ValueError, TypeError):
                            price = 0.0

                    worksheet.write(row, 2, price, money_format)
                    worksheet.write(row, 3, price * quantity, money_format)
                    row += 1

            # Write totals
            total_amount = 0.0
            if hasattr(order, "total_amount"):
                try:
                    total_amount = (
                        float(order.total_amount)
                        if order.total_amount is not None
                        else 0.0
                    )
                except (ValueError, TypeError):
                    total_amount = 0.0

            worksheet.write(row + 1, 2, "Total Amount:", bold)
            worksheet.write(row + 1, 3, total_amount, money_format)

            # Set column widths
            worksheet.set_column("A:A", 30)
            worksheet.set_column("B:D", 15)

            # Close workbook explicitly
            workbook.close()

            # Rewind the buffer and get its contents
            output.seek(0)
            content = output.getvalue()

            # Set up the HttpResponse with proper headers
            response = HttpResponse(
                content,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            filename = f"Receipt-{order.order_number}.xlsx"
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            response["Content-Length"] = len(content)

            # Return the response
            return response

        except Exception as inner_e:
            import traceback

            print(f"Inner error in Excel generation: {str(inner_e)}")
            print(traceback.format_exc())
            return HttpResponse(f"Error generating Excel: {str(inner_e)}", status=500)

    except Order.DoesNotExist:
        return HttpResponse("Order not found", status=404)
    except Exception as e:
        # Log the error with full traceback
        import traceback

        print(f"Error generating receipt: {str(e)}")
        print(traceback.format_exc())
        return HttpResponse(f"Error generating receipt: {str(e)}", status=500)
