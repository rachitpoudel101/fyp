# users/views.py
from profile import Profile
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm
from .models import CustomUser
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.urls import reverse
from django.shortcuts import get_object_or_404

def verify_email(request, token):
    profile = get_object_or_404(Profile, verification_token=token)
    profile.user.is_email_verified = True
    profile.user.save()
    profile.verification_token = None  # Invalidate the token
    profile.save()
    return render(request, 'email_verified.html')

def verify_pending(request):
    return render(request, 'verify_pending.html')

def generate_verification_token():
    return get_random_string(length=32)
# Sign up view - Allows users to register with a role
def signup(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.is_email_verified = False  # Set to False until verified
            user.save()

            # Generate email verification token
            token = generate_verification_token()
            user.profile.verification_token = token
            user.profile.save()

            # Send verification email
            verification_link = request.build_absolute_uri(
                reverse('verify_email', args=[token])
            )
            send_mail(
                'Verify your email',
                f'Click the link to verify your email: {verification_link}',
                'noreply@yourdomain.com',
                [user.email],
            )

            return redirect('login')  # Redirect after signup
    else:
        form = CustomUserCreationForm()
    return render(request, 'signup.html', {'form': form})


def user_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)  # Log the user in
            print(user.role)  # Log the role to check if it's correct
            if user.role == 'admin':
                return redirect('admin_dashboard')
            elif user.role == 'warehouse_manager':
                return redirect('warehouse_dashboard')
            else:
                return HttpResponseForbidden("You do not have permission to view this page.")
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

# Logout view - Logs users out and redirects to login page
def user_logout(request):
    logout(request)
    return redirect('login')  # Redirect to login after logout

# Dashboard view - Redirects users to role-based dashboards
@login_required
def dashboard(request):
    if request.user.role == 'admin':
        return redirect('admin_dashboard')
    elif request.user.role == 'warehouse_manager':
        return redirect('warehouse_dashboard')
    else:
        return HttpResponseForbidden("You do not have permission to view this page.")

# Admin Dashboard - Only accessible by admin users
@login_required
def admin_dashboard(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden("You are not authorized to view this page")
    warehouse_managers = CustomUser.objects.filter(role='warehouse_manager')
    return render(request, 'admin_dashboard.html', {'users': warehouse_managers})

# Warehouse Manager Dashboard - Only accessible by warehouse manager users
@login_required
def warehouse_dashboard(request):
    if request.user.role != 'warehouse_manager':
        return HttpResponseForbidden("You do not have permission to view this page.")
    return render(request, 'warehouse_dashboard.html')
