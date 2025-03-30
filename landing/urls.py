from django.urls import path
from landing.views import Index
from .views import home
from . import views

urlpatterns = [
    path('', home, name='home'),
    path('terms/', views.terms_view, name='terms'),
    path('privacy/', views.privacy_view, name='privacy'),
]
