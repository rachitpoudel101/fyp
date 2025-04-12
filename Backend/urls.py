from django.contrib import admin
from django.urls import path, include
from user import views as user_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('user/', include('user.urls')),
    path('inventory/', include('Inventory.urls')),
    path('', user_views.landing_page, name='landing_page'),
    path('profile/', user_views.profile_view, name='profile'),
    path('account_settings/', user_views.account_settings, name='account_settings'),
    path('change_password/', user_views.change_password, name='change_password'),
    path('super_admin_profile/', user_views.super_admin_profile, name='super_admin_profile'),
    path('forgot_password/', user_views.forgot_password, name='forgot_password'),
    path('reset_password/<str:token>/', user_views.reset_password, name='reset_password'),
    path('checkout/', user_views.checkout, name='checkout'),
    path('product_catalog/', user_views.product_catalog, name='product_catalog'),
    path('get_category_details/<int:category_id>/', user_views.get_category_details, name='get_category_details'),
    
    # Warehouse manager specific URLs
    path('warehouse/orders/', user_views.warehouse_orders, name='warehouse_orders'),
    path('notifications/', user_views.view_notifications, name='view_notifications'),
]