from django.urls import path
from .views import (
    HelloProtectedView,
    CustomTokenObtainPairView,
    CookieTokenObtainPairView,
    WhoAmIView,
    AdminProductListView,
    AdminUserListView,
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/cookie/', CookieTokenObtainPairView.as_view(), name='token_obtain_pair_cookie'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('hello/', HelloProtectedView.as_view(), name='hello_protected'),
    path('whoami/', WhoAmIView.as_view(), name='whoami'),
    path('admin/products/', AdminProductListView.as_view(), name='admin_products'),
    path('admin/users/', AdminUserListView.as_view(), name='admin_users'),
]
