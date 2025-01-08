# users/admin.py
from django.contrib import admin
from .models import CustomUser

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_active')  # Customize this as needed
    search_fields = ('username', 'email')

admin.site.register(CustomUser, CustomUserAdmin)
