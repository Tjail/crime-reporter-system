from django.shortcuts import render, redirect
from django.views import View

class Index(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'landing/index.html')

def custom_redirect(request):
    if request.user.is_authenticated:
        return redirect('post_list')  # Change this to wherever you want logged-in users to go
    return redirect('index')  # Change this to your home page

def home(request):
    return render(request, 'landing/home.html')

def terms_view(request):
    return render(request, 'landing/terms.html')

def privacy_view(request):
    return render(request, 'landing/privacy.html')