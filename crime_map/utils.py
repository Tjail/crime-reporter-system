from math import radians, sin, cos, sqrt, atan2
from datetime import timedelta
from django.utils import timezone
from .models import SuspiciousPin

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two points in kilometers using Haversine formula
    """
    try:
        lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return 6371 * c
    except (TypeError, ValueError):
        return float('inf')

def get_crime_stats(latitude, longitude, radius_km):
    """
    Get crime statistics for an area
    """
    
    stats = {
        'total_reports': 0,
        'recent_reports': 0,
        'crime_types': {},
        'time_distribution': {}
    }
    
    all_pins = SuspiciousPin.objects.all()
    nearby_pins = []
    
    for pin in all_pins:
        distance = calculate_distance(latitude, longitude, pin.latitude, pin.longitude)
        if distance <= radius_km:
            nearby_pins.append(pin)
    
    stats['total_reports'] = len(nearby_pins)
    
    recent_pins = [pin for pin in nearby_pins 
                  if pin.created_at >= timezone.now() - timedelta(days=30)]
    stats['recent_reports'] = len(recent_pins)
    
    return stats

from math import radians, sin, cos, sqrt, atan2
from django.utils import timezone
from datetime import timedelta
from .models import PinDrop, HotZone

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two points in kilometers using Haversine formula
    """
    try:
        lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return 6371 * c  # Earth radius in km
    except (TypeError, ValueError):
        return float('inf')

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
