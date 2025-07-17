from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.contrib.gis.geos import Point
from .models import SuspiciousPin, HotZone
from .forms import PinDropForm
import json

@login_required
def map_view(request):
    # Get recent pins (last 30 days)
    pins = SuspiciousPin.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=30)
    ).order_by('-created_at')
    
    # Get active hotzones
    hotzones = HotZone.objects.filter(
        resolved=False,
        expires_at__gte=timezone.now()
    )
    
    # Prepare data for frontend
    pin_data = [{
        'lat': pin.latitude,
        'lng': pin.longitude,
        'message': pin.message or '',
        'username': 'Anonymous' if pin.is_anonymous else pin.user.username,
        'date': pin.created_at.strftime('%Y-%m-%d %H:%M')
    } for pin in pins]
    
    hotzone_data = [{
        'lat': zone.latitude,
        'lng': zone.longitude,
        'radius': zone.radius,
        'level': zone.alert_level,
        'description': zone.get_alert_level_display()
    } for zone in hotzones]
    
    context = {
        'pin_data': json.dumps(pin_data),
        'hotzone_data': json.dumps(hotzone_data),
        'default_lat': -26.2041,  # Johannesburg
        'default_lng': 28.0473
    }
    
    return render(request, 'crime_map/map.html', context)

@login_required
def drop_pin(request):
    # Limit users to one pin per week
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
            # Create new pin
            pin = SuspiciousPin(
                user=request.user,
                location=form.cleaned_data['location'],
                message=form.cleaned_data['message'],
                is_anonymous=form.cleaned_data['is_anonymous']
            )
            pin.save()
            
            # Check if this creates a hotzone
            check_hotzone_creation(pin)
            
            messages.success(request, "Report submitted. Thank you for making your community safer!")
            return redirect('crime_map')
    else:
        form = PinDropForm()
    
    return render(request, 'crime_map/drop_pin.html', {'form': form})

def check_hotzone_creation(new_pin):
    """Check if enough reports exist to create a hotzone"""
    from django.contrib.gis.measure import D
    from django.contrib.gis.geos import Point
    
    # Find nearby pins within 1.5km radius (last 30 days)
    nearby_pins = SuspiciousPin.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=30),
        location__distance_lte=(new_pin.location, D(km=1.5))
    ).exclude(id=new_pin.id)
    
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
    
    # Check for existing overlapping hotzone
    existing_zone = HotZone.objects.filter(
        resolved=False,
        center__distance_lte=(new_pin.location, D(km=1.5))
    ).first()
    
    if existing_zone:
        if existing_zone.alert_level < alert_level:
            existing_zone.alert_level = alert_level
            existing_zone.save()
    else:
        HotZone.objects.create(
            center=new_pin.location,
            radius=1.5,
            alert_level=alert_level
        )