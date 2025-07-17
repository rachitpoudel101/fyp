from django.http import HttpResponseForbidden, HttpResponse
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    CreateView,
    UpdateView,
    DeleteView,
    ListView,
    DetailView,
    View,
)
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from user.models import Cart, Wishlist
from .models import Order, OrderItem, Product, Category
from .forms import OrderForm, ProductForm, CategoryForm
import io
import xlsxwriter


class CreateOrderView(LoginRequiredMixin, CreateView):
    model = Order
    form_class = OrderForm
    template_name = "create_order.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != "customer":
            return HttpResponseForbidden("You are not authorized to view this page")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.customer = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("order_detail", kwargs={"order_id": self.object.id})


class UpdateOrderStatusView(LoginRequiredMixin, UpdateView):
    model = Order
    form_class = OrderForm
    template_name = "update_order_status.html"
    pk_url_kwarg = "order_id"
    context_object_name = "order"

    def get_success_url(self):
        return reverse("order_detail", kwargs={"order_id": self.object.id})


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = "order_detail.html"
    pk_url_kwarg = "order_id"
    context_object_name = "order"

    def dispatch(self, request, *args, **kwargs):
        order = self.get_object()

        # Allow customer who placed the order to view it
        if request.user.role == "customer" and order.customer == request.user:
            return super().dispatch(request, *args, **kwargs)

        # Allow warehouse manager to view if order contains products from their warehouse
        elif (
            request.user.role == "warehouse_manager" and request.user.managed_warehouse
        ):
            order_items = OrderItem.objects.filter(
                order=order, product__warehouse=request.user.managed_warehouse
            )
            if order_items.exists():
                return super().dispatch(request, *args, **kwargs)

        # For admins and superadmins
        elif request.user.role in ["admin", "super_admin"]:
            return super().dispatch(request, *args, **kwargs)

        return HttpResponseForbidden("You are not authorized to view this page")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if (
            self.request.user.role == "warehouse_manager"
            and self.request.user.managed_warehouse
        ):
            order_items = OrderItem.objects.filter(
                order=self.object,
                product__warehouse=self.request.user.managed_warehouse,
            )
            context["warehouse_items"] = order_items
        return context


class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = "order_list.html"
    context_object_name = "orders"

    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in [
            "customer",
            "warehouse_manager",
            "admin",
            "super_admin",
        ]:
            return HttpResponseForbidden("You are not authorized to view this page")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if self.request.user.role == "customer":
            return Order.objects.filter(customer=self.request.user)
        elif (
            self.request.user.role == "warehouse_manager"
            and self.request.user.managed_warehouse
        ):
            managed_warehouse = self.request.user.managed_warehouse
            order_ids = (
                OrderItem.objects.filter(product__warehouse=managed_warehouse)
                .values_list("order_id", flat=True)
                .distinct()
            )
            return Order.objects.filter(id__in=order_ids).order_by("-created_at")
        elif self.request.user.role in ["admin", "super_admin"]:
            return Order.objects.all()
        return Order.objects.none()

    def get_template_names(self):
        if self.request.user.role == "warehouse_manager":
            return ["warehouse_orders.html"]
        return ["order_list.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.role == "customer":
            products = Product.objects.all()
            cart, _ = Cart.objects.get_or_create(user=self.request.user)
            wishlist, _ = Wishlist.objects.get_or_create(user=self.request.user)
            context.update(
                {
                    "products": products,
                    "cart": cart,
                    "wishlist": wishlist,
                }
            )
        elif self.request.user.role == "warehouse_manager":
            context["warehouse"] = self.request.user.managed_warehouse
        return context


class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = "products.html"
    context_object_name = "products"

    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ["admin"]:
            return HttpResponseForbidden("You are not authorized to view this page")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()

        expired_products = Product.objects.filter(
            expires__isnull=False, expires__lt=now
        ).order_by("expires")

        non_expired_products = Product.objects.filter(
            Q(expires__isnull=True) | Q(expires__gte=now)
        ).order_by("-created_at")

        context.update(
            {
                "expired_products": expired_products,
                "non_expired_products": non_expired_products,
                "total_products": Product.objects.count(),
                "expired_count": expired_products.count(),
                "non_expired_count": non_expired_products.count(),
            }
        )
        return context


class AddProductView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "add_product.html"
    success_url = reverse_lazy("products")

    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ["admin"]:
            return HttpResponseForbidden("You are not authorized to view this page")

        if not Category.objects.exists():
            messages.warning(
                request,
                "You need to create at least one category before adding products.",
            )
            return redirect("add_category")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Product added successfully!")
        return super().form_valid(form)


class UpdateProductView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "update_product.html"
    pk_url_kwarg = "product_id"
    context_object_name = "product"
    success_url = reverse_lazy("products")

    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ["admin"]:
            return HttpResponseForbidden("You are not authorized to view this page")
        return super().dispatch(request, *args, **kwargs)


class DeleteProductView(LoginRequiredMixin, DeleteView):
    model = Product
    template_name = "delete_product.html"
    pk_url_kwarg = "product_id"
    context_object_name = "product"
    success_url = reverse_lazy("products")

    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ["admin"]:
            return HttpResponseForbidden("You are not authorized to view this page")
        return super().dispatch(request, *args, **kwargs)


class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = "categories.html"
    context_object_name = "categories"

    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ["admin"]:
            return HttpResponseForbidden("You are not authorized to view this page")
        return super().dispatch(request, *args, **kwargs)


class AddCategoryView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "add_category.html"
    success_url = reverse_lazy("categories")

    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ["admin"]:
            return HttpResponseForbidden("You are not authorized to view this page")
        return super().dispatch(request, *args, **kwargs)


class UpdateCategoryView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "update_category.html"
    pk_url_kwarg = "category_id"
    context_object_name = "category"
    success_url = reverse_lazy("categories")

    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ["admin"]:
            return HttpResponseForbidden("You are not authorized to view this page")
        return super().dispatch(request, *args, **kwargs)


class DeleteCategoryView(LoginRequiredMixin, DeleteView):
    model = Category
    template_name = "delete_category.html"
    pk_url_kwarg = "category_id"
    context_object_name = "category"
    success_url = reverse_lazy("categories")

    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ["admin"]:
            return HttpResponseForbidden("You are not authorized to view this page")
        return super().dispatch(request, *args, **kwargs)


class DownloadReceiptView(View):
    def get(self, request, order_id):
        """Generate and download an Excel receipt for an order"""
        try:
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
                money_format = workbook.add_format(
                    {"border": 1, "num_format": "$#,##0.00"}
                )
                workbook.add_format({"num_format": "yyyy-mm-dd hh:mm"})

                # Write receipt header
                worksheet.merge_range("A1:E1", "ORDER RECEIPT", title)
                worksheet.write("A3", "Order Number:", bold)
                worksheet.write("B3", str(order.order_number))
                worksheet.write("A4", "Date:", bold)
                worksheet.write("B4", order.created_at.strftime("%Y-%m-%d %H:%M"))
                worksheet.write("A5", "Customer:", bold)
                customer_name = (
                    order.customer.get_full_name() if order.customer else "Guest"
                )
                worksheet.write("B5", str(customer_name))
                worksheet.write("A6", "Status:", bold)
                worksheet.write("B6", str(order.status).title())

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
                        quantity = (
                            int(item.quantity) if hasattr(item, "quantity") else 0
                        )
                        worksheet.write(row, 1, quantity, cell_format)

                        # Safely get the price as a float
                        price = 0.0
                        if hasattr(item, "price"):
                            try:
                                price = (
                                    float(item.price) if item.price is not None else 0.0
                                )
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

                return response

            except Exception as inner_e:
                import traceback

                print(f"Inner error in Excel generation: {str(inner_e)}")
                print(traceback.format_exc())
                return HttpResponse(
                    f"Error generating Excel: {str(inner_e)}", status=500
                )

        except Order.DoesNotExist:
            return HttpResponse("Order not found", status=404)
        except Exception as e:
            import traceback

            print(f"Error generating receipt: {str(e)}")
            print(traceback.format_exc())
            return HttpResponse(f"Error generating receipt: {str(e)}", status=500)


# Legacy function-based view aliases for backward compatibility (if needed)
create_order = CreateOrderView.as_view()
update_order_status = UpdateOrderStatusView.as_view()
order_detail = OrderDetailView.as_view()
order_list = OrderListView.as_view()
products = ProductListView.as_view()
add_product = AddProductView.as_view()
update_product = UpdateProductView.as_view()
delete_product = DeleteProductView.as_view()
categories = CategoryListView.as_view()
add_category = AddCategoryView.as_view()
update_category = UpdateCategoryView.as_view()
delete_category = DeleteCategoryView.as_view()
download_receipt = DownloadReceiptView.as_view()
