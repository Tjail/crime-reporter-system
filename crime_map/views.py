from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from .models import SuspiciousPin, HotZone
from .forms import PinDropForm
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
        'lat': pin.location.y,
        'lng': pin.location.x,
        'message': pin.message or '',
        'username': 'Anonymous' if pin.is_anonymous else pin.user.username,
        'date': pin.created_at.strftime('%Y-%m-%d %H:%M')
    } for pin in pins]
    
    hotzone_data = [{
        'lat': zone.center.y,
        'lng': zone.center.x,
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
                location=form.cleaned_data['location'],
                message=form.cleaned_data['message'],
                is_anonymous=form.cleaned_data['is_anonymous']
            )
            pin.save()
            
            check_hotzone_creation(pin.location)
            
            messages.success(request, "Report submitted. Thank you for making your community safer!")
            return redirect('crime_map')
    else:
        form = PinDropForm()
    
    return render(request, 'crime_map/drop_pin.html', {'form': form})

def check_hotzone_creation(point, radius_km=1.5):
    """Check if enough reports exist to create a hotzone"""
    from django.contrib.gis.measure import D
    
    unique_users = SuspiciousPin.objects.filter(
        location__distance_lte=(point, D(km=radius_km)),
        created_at__gte=timezone.now() - timedelta(days=30)
    ).values_list('user', flat=True).distinct()
    
    user_count = len([u for u in unique_users if u])
    
    if user_count >= 20:
        alert_level = 3
    elif user_count >= 10:
        alert_level = 2
    elif user_count >= 5:
        alert_level = 1
    else:
        return
    
    existing_zone = HotZone.objects.filter(
        center__distance_lte=(point, D(km=radius_km)),
        resolved=False
    ).first()
    
    if existing_zone:
        if existing_zone.alert_level < alert_level:
            existing_zone.alert_level = alert_level
            existing_zone.save()
    else:
        HotZone.objects.create(
            center=point,
            radius=radius_km,
            alert_level=alert_level
        )
