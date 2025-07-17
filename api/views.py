from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework import status
from user.models import CustomUser
from Inventory.models import Product

# Create your views here.

class HelloProtectedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"message": f"Hello, {request.user.username}! This is a protected API."})

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer

class CookieTokenObtainPairView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            response = Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            })
            # Set HttpOnly cookies
            response.set_cookie(
                key="access_token",
                value=str(refresh.access_token),
                httponly=True,
                samesite="Lax",
                secure=False,  # Set to True in production with HTTPS
                max_age=60 * 60,  # 1 hour
            )
            response.set_cookie(
                key="refresh_token",
                value=str(refresh),
                httponly=True,
                samesite="Lax",
                secure=False,  # Set to True in production with HTTPS
                max_age=7 * 24 * 60 * 60,  # 7 days
            )
            return response
        return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

class WhoAmIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
        }
        return Response(data)

class AdminProductListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role != "admin" and not user.is_superuser:
            return Response({"detail": "Forbidden"}, status=403)
        products = Product.objects.all().values("id", "name", "price", "stock", "description")
        return Response(list(products))

class AdminUserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role != "admin" and not user.is_superuser:
            return Response({"detail": "Forbidden"}, status=403)
        users = CustomUser.objects.all().values("id", "username", "email", "role", "is_active")
        return Response(list(users))
