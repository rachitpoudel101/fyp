from django.urls import path
from . import views

urlpatterns = [
    # Authentication URLs
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('profile/', views.profile_view, name='profile_view'),
    
    # Staff panel URLs
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/orders/', views.staff_order_management, name='staff_order_management'),
    path('staff/deliveries/', views.staff_deliveries, name='staff_deliveries'),
    path('staff/inventory/', views.staff_inventory_management, name='staff_inventory_management'),
    path('staff/customers/', views.staff_customer_management, name='staff_customer_management'),
    path('staff/update-stock/<int:product_id>/', views.staff_update_stock, name='staff_update_stock'),
    path('update-delivery/<int:order_id>/', views.update_delivery_status, name='update_delivery_status'),
    
    # Add other URL patterns that may already be in your file
    path('', views.landing_page, name='landing_page'),  # Add this line at the top
    # User authentication URLs
    path('signup/', views.signup, name='signup'),  # Signup URL
    path('logout/', views.user_logout, name='logout'),  # Logout URL

    # Dashboard URLs
    path('dashboard/', views.dashboard, name='dashboard'),  # General user dashboard
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),  # Admin dashboard
    path('warehouse-dashboard/', views.warehouse_dashboard, name='warehouse_dashboard'),  # Warehouse dashboard
    path('super_admin_dashboard/', views.super_admin_dashboard, name='super_admin_dashboard'),  # Super Admin dashboard
    path('customer/dashboard/', views.customer_dashboard, name='customer_dashboard'),  # Customer dashboard
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),  # Staff dashboard

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
    path('account-settings/', views.account_settings, name='account_settings'),
    path('change-password/', views.change_password, name='change_password'),
    path('super-admin-profile/', views.super_admin_profile, name='super_admin_profile'),

    # Password reset URLs
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),

    # Cart URLs
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    
    # Wishlist URLs
    path('wishlist/', views.view_wishlist, name='view_wishlist'),
    path('wishlist/add/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/move-to-cart/', views.move_to_cart, name='move_to_cart'),

    # Add the checkout URL pattern
    path('checkout/', views.checkout, name='checkout'),

    # Customer product catalog
    path('products/', views.product_catalog, name='product_catalog'),

    # New API endpoint to get category details
    path('category/<int:category_id>/', views.get_category_details, name='get_category_details'),

    # Add the new API endpoint for warehouse product count
    path('api/warehouse/<int:warehouse_id>/product-count/', views.warehouse_product_count, name='warehouse_product_count'),

    # Add the new API endpoint for updating stock
    path('update-stock/<int:product_id>/', views.update_stock, name='update_stock'),

    # Add the new Khalti payment verification URL
    path('verify-khalti-payment/', views.verify_khalti_payment, name='verify_khalti_payment'),

    # Staff-related URLs
    path('staff/orders/', views.staff_order_management, name='staff_order_management'),
    path('staff/deliveries/', views.staff_deliveries, name='staff_deliveries'),
    path('staff/inventory/', views.staff_inventory_management, name='staff_inventory_management'),
    path('staff/customers/', views.staff_customer_management, name='staff_customer_management'),
    path('staff/update-stock/<int:product_id>/', views.staff_update_stock, name='staff_update_stock'),
    path('staff/update-delivery/<int:order_id>/', views.update_delivery_status, name='update_delivery_status'),

    # Add this new URL pattern for assigning staff to orders
    path('assign-staff-to-order/<int:order_id>/', views.assign_staff_to_order, name='assign_staff_to_order'),

    # Make sure these existing URLs are properly configured
    path('warehouse/orders/', views.warehouse_orders, name='warehouse_orders'),
    path('update-delivery-status/<int:order_id>/', views.update_delivery_status, name='update_delivery_status'),

    # Profile and account settings URLs
    path('account-settings/', views.account_settings, name='account_settings'),
    path('change-password/', views.change_password, name='change_password'),
    path('super-admin-profile/', views.super_admin_profile, name='super_admin_profile'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
    
    # Product related URLs
    path('get-category-details/<int:category_id>/', views.get_category_details, name='get_category_details'),
    
    # Notification URL
    path('notifications/', views.view_notifications, name='view_notifications'),
    
    # Billing export routes
    path('export-billing/', views.export_billing, name='export_billing'),
    path('export-billing/<int:order_id>/', views.export_billing, name='export_billing_order'),
    
    # Email bill route
    path('email-bill/<int:order_id>/', views.email_bill, name='email_bill'),
]
