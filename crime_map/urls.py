from django.urls import path
from .views import map_view, drop_pin, hotzone_detail, pin_drop_location

urlpatterns = [
    path('', map_view, name='crime_map'),
    path('drop/', drop_pin, name='drop_pin'),
    path('pin-drop/', pin_drop_location, name='pin_drop_location'),
    path('hotzone/<int:pk>/', hotzone_detail, name='hotzone_detail'),
]