from django.urls import path
from .views import admin_add_product, warehouse_manager_panel

urlpatterns = [
    path('admin/add_product/', admin_add_product, name='admin_add_product'),
    path('warehouse_manager/', warehouse_manager_panel, name='warehouse_manager_panel'),
]