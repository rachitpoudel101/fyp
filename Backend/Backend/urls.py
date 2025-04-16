from django.contrib import admin
from django.urls import path, include
from user import views as user_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('user/', include('user.urls')),
    path('order_dashboard/', user_views.order_dashboard, name='order_dashboard'),
]