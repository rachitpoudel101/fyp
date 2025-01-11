from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import Product, Batch
from .forms import ProductForm

# @login_required
def admin_add_product(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden("You are not authorized to view this page")
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('admin_add_product')
    else:
        form = ProductForm()
    return render(request, 'admin_add_product.html', {'form': form})

# @login_required
def warehouse_manager_panel(request):
    if request.user.role != 'warehouse_manager':
        return HttpResponseForbidden("You are not authorized to view this page")
    products = Product.objects.all()
    return render(request, 'warehouse_dashboard.html', {'products': products})