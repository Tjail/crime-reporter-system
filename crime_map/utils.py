from math import radians, sin, cos, sqrt, atan2

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points
    on Earth (specified in decimal degrees) using Haversine formula.
    Returns distance in kilometers.
    """
    # Convert decimal degrees to radians 
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    # Radius of Earth in kilometers
    R = 6371
    return R * c

def get_points_in_radius(latitude, longitude, radius_km, queryset):
    """
    Filter a queryset of location objects to find those within radius_km
    of the given latitude/longitude point.
    """
    nearby = []
    for obj in queryset:
        distance = calculate_distance(latitude, longitude, 
                                    obj.latitude, obj.longitude)
        if distance <= radius_km:
            nearby.append(obj)
    return nearby

def calculate_distance(lat1, lon1, lat2, lon2):
    try:
        # Convert to float first
        lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
        # Rest of calculation...
    except (TypeError, ValueError):
        return float('inf')