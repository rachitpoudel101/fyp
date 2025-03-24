from django import forms
from .models import Warehouse, CustomUser

class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = ['name', 'location']

class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'role']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make email field required
        self.fields['email'].required = True
        
        # Set role choices
        if 'role' in self.fields:
            self.fields['role'].choices = [
                ('admin', 'Admin'),
                ('warehouse_manager', 'Warehouse Manager'),
            ]
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            if CustomUser.objects.filter(email=email).exists():
                raise forms.ValidationError("Email already exists")
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            if CustomUser.objects.filter(username=username).exists():
                raise forms.ValidationError("Username already exists")
        return username
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        
        # Always ensure role is 'admin'
        user.role = 'admin'
        
        if commit:
            user.save()
        return user