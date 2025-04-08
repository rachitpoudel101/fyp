from django.urls import path
from . import views
from .views import add_user

urlpatterns = [
    path('', views.landing_page, name='landing_page'),  # Add this line at the top
    # User authentication URLs
    path('signup/', views.signup, name='signup'),  # Signup URL
    path('login/', views.user_login, name='login'),  # Login URL
    path('logout/', views.user_logout, name='logout'),  # Logout URL

    # Dashboard URLs
    path('dashboard/', views.dashboard, name='dashboard'),  # General user dashboard
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),  # Admin dashboard
    path('warehouse-dashboard/', views.warehouse_dashboard, name='warehouse_dashboard'),  # Warehouse dashboard
    path('super_admin_dashboard/', views.super_admin_dashboard, name='super_admin_dashboard'),  # Super Admin dashboard
    path('customer/dashboard/', views.customer_dashboard, name='customer_dashboard'),  # Customer dashboard

    # Inventory and orders management URLs
    path('inventory/', views.inventory, name='inventory'),  # Inventory management (Admin/Warehouse)
    path('orders/', views.orders, name='orders'),  # Orders management (Admin/Warehouse)
    path('update_order_status/<int:order_id>/', views.update_order_status, name='update_order_status'),  # Update order status (Admin/Warehouse)
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),  # Email verification (Customer)
    path('verify-pending/', views.verify_pending, name='verify_pending'),  # Pending verification (Customer)
    path('resend-verification-email/', views.resend_verification_email, name='resend_verification_email'),  # Resend verification email (Customer)
    path('request-verification/', views.request_verification, name='request_verification'),  # Request verification (Customer)

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
    path('edit-category/<int:category_id>/', views.edit_category, name='edit_category'),
    path('delete-category/<int:category_id>/', views.delete_category, name='delete_category'),
    path('manage-categories/', views.manage_categories, name='manage_categories'),
    path('billing/', views.billing, name='billing'),  # Billing management (Admin)

    # Warehouse management URLs
    path('create_warehouse/', views.create_warehouse, name='create_warehouse'),  # Create warehouse (Admin)
    path('manage_warehouses/', views.manage_warehouses, name='manage_warehouses'),  # Manage warehouses (Admin)
    path('edit_warehouse/<int:warehouse_id>/', views.edit_warehouse, name='edit_warehouse'),  # Add this line
    path('delete-warehouse/<int:warehouse_id>/', views.delete_warehouse, name='delete_warehouse'),  # Add this line
    path('add-warehouse-manager/', views.add_warehouse_manager, name='add_warehouse_manager'),  # Add warehouse manager URL
    path('add-staff/', views.add_staff, name='add_staff'),  # Add staff URL
    path('assign-warehouse-manager/<int:warehouse_id>/', views.assign_warehouse_manager, name='assign_warehouse_manager'),
    path('warehouse/<int:warehouse_id>/products/', views.warehouse_products, name='warehouse_products'),
    path('delete_product/<int:product_id>/', views.delete_product, name='delete_product'),

    # Add user URLs
    path('add_user/', views.add_user, name='add_user'),  # Existing API endpoint
    path('add_user_page/', views.add_user_page, name='add_user_page'),  # New page view
    path('add_admin/', views.add_admin, name='add_admin'),  # Add admin URL

    # New admin approval and verification URLs
    path('approve-admin/<int:admin_id>/', views.approve_admin, name='approve_admin'),
    path('verify-admin/<int:admin_id>/', views.verify_admin, name='verify_admin'),

    # Admin management URLs
    path('admin-management/', views.admin_management, name='admin_management'),  # Admin management page
    path('edit-admin/<int:admin_id>/', views.edit_admin, name='edit_admin'),  # Edit admin
    path('delete-admin/<int:admin_id>/', views.delete_admin, name='delete_admin'),  # Delete admin
    path('change-admin-password/<int:admin_id>/', views.change_admin_password, name='change_admin_password'),
    path('toggle-admin-status/<int:admin_id>/', views.toggle_admin_status, name='toggle_admin_status'),

    # Profile URL
    path('profile/', views.profile_view, name='profile'),
    path('super-admin-profile/', views.super_admin_profile, name='super_admin_profile'),

    # Password reset URLs
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
]