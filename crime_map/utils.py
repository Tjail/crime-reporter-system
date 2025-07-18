from math import radians, sin, cos, sqrt, atan2
from datetime import timedelta
from django.utils import timezone
from .models import PinDrop

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
    Get crime statistics for an area (now using PinDrop instead of SuspiciousPin)
    """
    stats = {
        'total_reports': 0,
        'recent_reports': 0,
        'crime_types': {},
        'time_distribution': {}
    }
    
    all_pins = PinDrop.objects.all()
    nearby_pins = []
    
    for pin in all_pins:
        distance = calculate_distance(latitude, longitude, pin.latitude, pin.longitude)
        if distance <= radius_km:
            nearby_pins.append(pin)
    
    stats['total_reports'] = len(nearby_pins)
    
    recent_pins = [pin for pin in nearby_pins 
                  if pin.created_at >= timezone.now() - timedelta(days=30)]
    stats['recent_reports'] = len(recent_pins)
    
    for pin in nearby_pins:
        crime_type = pin.get_report_type_display()
        stats['crime_types'][crime_type] = stats['crime_types'].get(crime_type, 0) + 1
    
    return stats
