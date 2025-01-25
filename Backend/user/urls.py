# users/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('warehouse-dashboard/', views.warehouse_dashboard, name='warehouse_dashboard'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('verify-pending/', views.verify_pending, name='verify_pending'),
]

