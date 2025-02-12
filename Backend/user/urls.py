# users/urls.py
from django.urls import path
from . import views
from inventory import views as inventory_views

urlpatterns = [
    path('', views.signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('warehouse-dashboard/', views.warehouse_dashboard, name='warehouse_dashboard'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('verify-pending/', views.verify_pending, name='verify_pending'),

    path('create_order/', inventory_views.create_order, name='create_order'),
    path('update_order_status/<int:order_id>/', inventory_views.update_order_status, name='update_order_status'),
    path('order_detail/<int:order_id>/', inventory_views.order_detail, name='order_detail'),
    path('order_list/', inventory_views.order_list, name='order_list'),
]