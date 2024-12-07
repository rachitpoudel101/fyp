from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework import generic
from .serializers import UserSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny

class CreateUserView(generic.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = User
    permission_classes = [AllowAny]