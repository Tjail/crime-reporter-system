#This file is crime_map/urls.py
from django.urls import path
from .views import map_view, pin_drop, quick_pin, hotzone_detail, pin_drop_location
from . import views 

urlpatterns = [
    path('', views.map_view, name='crime_map'),
    path('pin-drop/', views.pin_drop_location, name='pin_drop_location'),
    path('report/', pin_drop, name='pin_drop'),
    path('quick-report/', quick_pin, name='quick_pin'),
    path('pin/<int:pk>/', views.pin_detail_view, name='pin_detail'),
    path('hotzone/<int:pk>/', views.hotzone_detail, name='hotzone_detail'),
]