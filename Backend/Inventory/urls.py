from django.urls import path
from . import views
from .views import admin_add_product, warehouse_manager_panel

urlpatterns = [
    path('admin/add_product/', admin_add_product, name='admin_add_product'),
    path('logout/', views.user_logout, name='user_logout'),
    path('warehouse_manager/', warehouse_manager_panel, name='warehouse_manager_panel'),
]