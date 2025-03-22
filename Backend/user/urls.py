from django.urls import path
from . import views
from .views import add_user

urlpatterns = [
    # User authentication URLs
    path('signup/', views.signup, name='signup'),  # Signup URL
    path('', views.user_login, name='login'),  # Login URL
    path('login/', views.user_login, name='login'),  # Add this line
    path('logout/', views.user_logout, name='logout'),  # Logout URL

    # Dashboard URLs
    path('dashboard/', views.dashboard, name='dashboard'),  # General user dashboard
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),  # Admin dashboard
    path('warehouse-dashboard/', views.warehouse_dashboard, name='warehouse_dashboard'),  # Warehouse dashboard
    path('super_admin_dashboard/', views.super_admin_dashboard, name='super_admin_dashboard'),  # Super Admin dashboard

    # Inventory and orders management URLs
    path('inventory/', views.inventory, name='inventory'),  # Inventory management (Admin/Warehouse)
    path('orders/', views.orders, name='orders'),  # Orders management (Admin/Warehouse)
    path('update_order_status/<int:order_id>/', views.update_order_status, name='update_order_status'),  # Update order status (Admin/Warehouse)
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),  # Email verification (Customer)
    path('verify-pending/', views.verify_pending, name='verify_pending'),  # Pending verification (Customer)
    path('resend-verification-email/', views.resend_verification_email, name='resend_verification_email'),  # Resend verification email (Customer)

    # Order creation and details URLs
    path('create_order/', views.create_order, name='create_order'),  # Create order (Customer)
    path('order_detail/<int:order_id>/', views.order_detail, name='order_detail'),  # Order detail (Customer)
    path('order_list/', views.order_list, name='order_list'),  # Order list (Customer)

    # User statistics URL
    path('user_statistics/', views.user_statistics, name='user_statistics'),  # User statistics (Admin)

    # Additional management URLs
    path('product_management/', views.product_management, name='product_management'),  # Product management (Admin)
    path('update-product/<int:product_id>/', views.update_product, name='update_product'),
    path('add-category/', views.add_category, name='add_category'),
    path('billing/', views.billing, name='billing'),  # Billing management (Admin)

    # Warehouse management URLs
    path('create_warehouse/', views.create_warehouse, name='create_warehouse'),  # Create warehouse (Admin)
    path('manage_warehouses/', views.manage_warehouses, name='manage_warehouses'),  # Manage warehouses (Admin)

    # Add user URL
    path('add_user/', add_user, name='add_user'),
    path('add_admin/', views.add_admin, name='add_admin'),  # Add admin URL
]