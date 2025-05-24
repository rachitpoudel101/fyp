from django.urls import path
from . import views

urlpatterns = [
    # Existing URLs
    path('order/create/', views.create_order, name='create_order'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('order/<int:order_id>/update/', views.update_order_status, name='update_order_status'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:order_id>/receipt/', views.download_receipt, name='download_receipt'),
    
    # # Admin Product Management
    # path('admin/products/', views.products, name='products'),
    # path('admin/products/add/', views.add_product, name='add_product'),
    # path('admin/products/<int:product_id>/update/', views.admin_update_product, name='admin_update_product'),
    # path('admin/products/<int:product_id>/delete/', views.admin_delete_product, name='admin_delete_product'),
    
    # # Admin Category Management
    # path('admin/categories/', views.categories, name='categories'),
    # path('admin/categories/add/', views.add_category, name='add_category'),
    # path('admin/categories/<int:category_id>/update/', views.update_category, name='update_category'),
    # path('admin/categories/<int:category_id>/delete/', views.delete_category, name='delete_category'),
]
