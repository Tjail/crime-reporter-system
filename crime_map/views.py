from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import HotZone, PinDrop
from .forms import PinDropForm
from .utils import calculate_distance
import json
from django.utils import timezone
from .forms import PinDropForm, QuickPinForm

@login_required
def pin_drop(request):
    """Detailed pin drop form"""
    last_pin = PinDrop.objects.filter(
        user=request.user,
        created_at__gte=timezone.now() - timedelta(days=1)
    ).first()
    
    if last_pin:
        messages.warning(request, "You can only submit one report per day")
        return redirect('crime_map')

    if request.method == 'POST':
        form = PinDropForm(request.POST)
        if form.is_valid():
            pin = form.save(commit=False)
            pin.user = request.user
            pin.save()
            
            check_hotzone_creation(pin)
            messages.success(request, "Report submitted successfully!")
            return redirect('crime_map')
    else:
        form = PinDropForm()
    
    return render(request, 'crime_map/pin_drop.html', {
        'form': form,
        'default_lat': -26.2041,
        'default_lng': 28.0473
    })

@login_required
def quick_pin(request):
    """Quick anonymous reporting"""
    if request.method == 'POST':
        form = QuickPinForm(request.POST)
        if form.is_valid():
            pin = PinDrop(
                user=request.user,
                latitude=form.cleaned_data['latitude'],
                longitude=form.cleaned_data['longitude'],
                report_type=form.cleaned_data['report_type'],
                message=form.cleaned_data['message'],
                is_anonymous=True
            )
            pin.save()
            
            check_hotzone_creation(pin)
            messages.success(request, "Anonymous report submitted. Thank you!")
            return redirect('crime_map')
    else:
        form = QuickPinForm()
    
    return render(request, 'crime_map/quick_pin.html', {
        'form': form,
        'default_lat': -26.2041,
        'default_lng': 28.0473
    })

@login_required
def map_view(request):
    # Get all pins (both detailed and quick reports)
    pins = PinDrop.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=30)
    ).order_by('-created_at')
    
    hotzones = HotZone.objects.filter(
        resolved=False,
        expires_at__gte=timezone.now()
    )
    
    # Prepare data for frontend
    pin_data = [{
        'lat': pin.latitude,
        'lng': pin.longitude,
        'type': pin.report_type,
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
def hotzone_detail(request, pk):
    """View details of a specific hotzone"""
    hotzone = get_object_or_404(HotZone, pk=pk)
    
    pins = PinDrop.objects.all()
    pins_in_zone = []
    for pin in pins:
        distance = calculate_distance(
            hotzone.latitude, hotzone.longitude,
            pin.latitude, pin.longitude
        )
        if distance <= hotzone.radius:
            pins_in_zone.append(pin)
    
    context = {
        'hotzone': hotzone,
        'pins': pins_in_zone,
    }
    return render(request, 'crime_map/hotzone_detail.html', context)

def check_hotzone_creation(new_pin):
    """Check if enough reports exist to create a hotzone"""
    recent_pins = PinDrop.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=30)
    ).exclude(id=new_pin.id)
    
    nearby_pins = []
    for pin in recent_pins:
        distance = calculate_distance(
            new_pin.latitude, new_pin.longitude,
            pin.latitude, pin.longitude
        )
        if distance <= 1.5:  # 1.5km radius
            nearby_pins.append(pin)
    
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
        distance = calculate_distance(
            new_pin.latitude, new_pin.longitude,
            zone.latitude, zone.longitude
        )
        if distance <= 1.5:
            existing_zone = zone
            break
    
    if existing_zone:
        if existing_zone.alert_level < alert_level:
            existing_zone.alert_level = alert_level
            existing_zone.save()
    else:
        HotZone.objects.create(
            latitude=new_pin.latitude,
            longitude=new_pin.longitude,
            radius=1.5,
            alert_level=alert_level
        )