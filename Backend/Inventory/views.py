from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Order, OrderItem, Product
from .forms import OrderForm, OrderItemForm

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
    if request.user.role != 'customer' or order.customer != request.user:
        return HttpResponseForbidden("You are not authorized to view this page")
    return render(request, 'order_detail.html', {'order': order})

@login_required
def order_list(request):
    if request.user.role != 'customer':
        return HttpResponseForbidden("You are not authorized to view this page")
    
    orders = Order.objects.filter(customer=request.user)
    return render(request, 'order_list.html', {'orders': orders})