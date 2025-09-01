#this file is landing/urls.py
from django.urls import path
from landing.views import Index
from .views import home, thank_you
from . import views

urlpatterns = [
    path('', home, name='home'),
    path('thank-you/', thank_you, name='thank_you'),
    path('terms/', views.terms_view, name='terms'),
    path('privacy/', views.privacy_view, name='privacy'),
]
