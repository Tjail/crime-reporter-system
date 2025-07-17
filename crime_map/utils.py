from math import radians, sin, cos, sqrt, atan2

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two points in kilometers
    (Fallback if GIS functions not available)
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

def get_crime_stats(center_point, radius_km):
    """
    Get crime statistics for an area
    """
    from django.contrib.gis.measure import D
    from .models import SuspiciousPin
    
    stats = {
        'total_reports': 0,
        'recent_reports': 0,
        'crime_types': {},
        'time_distribution': {}
    }
    
    # All reports in area
    all_reports = SuspiciousPin.objects.filter(
        location__distance_lte=(center_point, D(km=radius_km))
    )
    stats['total_reports'] = all_reports.count()
    
    # Recent reports (last 30 days)
    recent_reports = all_reports.filter(
        created_at__gte=timezone.now() - timedelta(days=30))
    stats['recent_reports'] = recent_reports.count()
    
    return stats
