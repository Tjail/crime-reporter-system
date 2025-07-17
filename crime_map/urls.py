from django.urls import path
from .views import map_view, pin_drop, quick_pin, hotzone_detail

urlpatterns = [
    path('', map_view, name='crime_map'),
    path('report/', pin_drop, name='pin_drop'),
    path('quick-report/', quick_pin, name='quick_pin'),
    path('hotzone/<int:pk>/', hotzone_detail, name='hotzone_detail'),
]