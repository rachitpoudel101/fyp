from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Warehouse, CustomUser

class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = ['name', 'location']

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES, initial='customer', widget=forms.HiddenInput())

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2', 'role')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = 'customer'  # Always set role to customer
        if commit:
            user.save()
        return user

class StaffCreationForm(CustomUserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].initial = 'staff'
        self.fields['role'].widget = forms.HiddenInput()
        self.fields['is_staff'] = forms.BooleanField(initial=True, widget=forms.HiddenInput())

class WarehouseManagerCreationForm(CustomUserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].initial = 'warehouse_manager'
        self.fields['role'].widget = forms.HiddenInput()
        self.fields['is_staff'] = forms.BooleanField(initial=True, widget=forms.HiddenInput())