from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import SuspiciousPin, HotZone
from .forms import PinDropForm
from .utils import calculate_distance, get_points_in_radius
import json

@login_required
def map_view(request):
    pins = SuspiciousPin.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=30)
    ).order_by('-created_at')
    
    hotzones = HotZone.objects.filter(
        resolved=False,
        expires_at__gte=timezone.now()
    )
    
    pin_data = [{
        'lat': pin.latitude,
        'lng': pin.longitude,
        'message': pin.message or '',
        'username': 'Anonymous' if pin.is_anonymous else pin.user.username,
        'date': pin.created_at.strftime('%Y-%m-%d %H:%M')
    } for pin in pins]
    
    hotzone_data = [{
        'lat': zone.center_latitude,
        'lng': zone.center_longitude,
        'radius': zone.radius,
        'level': zone.alert_level,
        'description': zone.get_alert_level_display()
    } for zone in hotzones]
    
    context = {
        'pin_data': json.dumps(pin_data),
        'hotzone_data': json.dumps(hotzone_data),
        'default_lat': -26.2041,
        'default_lng': 28.0473
    }
    
    return render(request, 'crime_map/map.html', context)

@login_required
def drop_pin(request):
    last_pin = SuspiciousPin.objects.filter(
        user=request.user,
        created_at__gte=timezone.now() - timedelta(days=7)
    ).first()
    
    if last_pin:
        messages.warning(request, 
            f"You can only drop one pin per week. Try again after {last_pin.created_at + timedelta(days=7):%Y-%m-%d}")
        return redirect('crime_map')
    
    if request.method == 'POST':
        form = PinDropForm(request.POST)
        if form.is_valid():
            pin = SuspiciousPin(
                user=request.user,
                latitude=form.cleaned_data['latitude'],
                longitude=form.cleaned_data['longitude'],
                message=form.cleaned_data['message'],
                is_anonymous=form.cleaned_data['is_anonymous']
            )
            pin.save()
            
            check_hotzone_creation(pin.latitude, pin.longitude)
            
            messages.success(request, "Report submitted. Thank you for making your community safer!")
            return redirect('crime_map')
    else:
        form = PinDropForm()
    
    return render(request, 'crime_map/drop_pin.html', {'form': form})

def check_hotzone_creation(latitude, longitude, radius_km=1.5):
    """Check if enough reports exist to create a hotzone"""
    from .models import SuspiciousPin, HotZone
    
    recent_pins = SuspiciousPin.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=30)
    )
    nearby_pins = get_points_in_radius(latitude, longitude, radius_km, recent_pins)
    
    unique_users = {pin.user for pin in nearby_pins if pin.user}
    
    user_count = len(unique_users)
    if user_count >= 20:
        alert_level = 3
    elif user_count >= 10:
        alert_level = 2
    elif user_count >= 5:
        alert_level = 1
    else:
        return
    
    existing_zone = None
    for zone in HotZone.objects.filter(resolved=False):
        distance = calculate_distance(latitude, longitude, 
                                    zone.center_latitude, zone.center_longitude)
        if distance <= radius_km:
            existing_zone = zone
            break
    
    if existing_zone:
        if existing_zone.alert_level < alert_level:
            existing_zone.alert_level = alert_level
            existing_zone.save()
    else:
        HotZone.objects.create(
            center_latitude=latitude,
            center_longitude=longitude,
            radius=radius_km,
            alert_level=alert_level
        )