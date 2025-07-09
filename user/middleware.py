# middleware.py
from django.shortcuts import redirect


class EmailVerificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_email_verified:
            return redirect("verify_pending")
        return self.get_response(request)
