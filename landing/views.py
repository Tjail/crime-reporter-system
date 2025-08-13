from django.shortcuts import render, redirect
from django.views import View
from social.models import AccountType

class Index(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'landing/index.html')

def custom_redirect(request):
    """Redirect users based on their account type after login"""
    if request.user.is_authenticated:
        if hasattr(request.user, 'account_type'):
            account = request.user.account_type
            
            # Redirect based on account type and verification status
            if account.account_type == AccountType.POLICE:
                if account.is_verified:
                    return redirect('police_dashboard')
                else:
                    return redirect('verification_pending')
            elif account.account_type == AccountType.SECURITY_COMPANY:
                if account.is_verified:
                    return redirect('security_dashboard')
                else:
                    return redirect('verification_pending')
            else:  # CITIZEN
                return redirect('post_list')
        else:
            # User doesn't have an account type (shouldn't happen with new system)
            return redirect('account_type_signup')
    return redirect('index')

def home(request):
    return render(request, 'landing/home.html')

def terms_view(request):
    return render(request, 'landing/terms.html')

def privacy_view(request):
    return render(request, 'landing/privacy.html')

def thank_you(request):
    return render(request, 'landing/thank_you.html')