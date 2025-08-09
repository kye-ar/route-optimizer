import math
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Union


def import_config(*names):
    """Centralized config import with fallback for different module contexts."""
    try:
        import importlib
        config = importlib.import_module('.config', package=__package__)
    except (ImportError, ValueError):
        import config
    
    if len(names) == 1:
        return getattr(config, names[0])
    return tuple(getattr(config, name) for name in names)


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance in miles between two points using Haversine formula."""
    # Haversine formula accounts for Earth's curvature - more accurate than Euclidean
    earth_radius_miles = 3963.1
    
    # Convert degrees to radians for trigonometric calculations
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    dlat, dlng = lat2 - lat1, lng2 - lng1
    
    # Standard Haversine formula calculation
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    return earth_radius_miles * c


def generate_google_maps_url(route_points: List[Tuple[float, float]]) -> str:
    """Generate Google Maps URL with route waypoints."""
    if len(route_points) < 2:
        return "Error: a route requires at least 2 points"

    url = "https://www.google.com/maps/dir/"
    for lat, lng in route_points:
        lat, lng = normalize_coordinates(lat, lng)
        url += f"{lat},{lng}/"
    
    return url


def add_minutes_to_time(time_str: str, minutes: int) -> str:
    """Add minutes to time string (HH:MM:SS format)."""
    time_obj = datetime.strptime(time_str, "%H:%M:%S")
    new_time = time_obj + timedelta(minutes=minutes)
    return new_time.strftime("%H:%M:%S")


def subtract_minutes_from_time(time_str: str, minutes: int) -> str:
    """Subtract minutes from time string (HH:MM:SS format)."""
    time_obj = datetime.strptime(time_str, "%H:%M:%S")
    new_time = time_obj - timedelta(minutes=minutes)
    return new_time.strftime("%H:%M:%S")


def time_difference_minutes(time1: str, time2: str) -> int:
    """Calculate difference in minutes between two times (time2 - time1)."""
    t1 = datetime.strptime(time1, "%H:%M:%S")
    t2 = datetime.strptime(time2, "%H:%M:%S")
    return int((t2 - t1).total_seconds() / 60)


def is_time_within_window(current_time: str, from_time: str, to_time: str) -> bool:
    """Check if current time falls within time window (inclusive)."""
    # Parse time strings and check if current time is within delivery window
    current = datetime.strptime(current_time, "%H:%M:%S")
    from_dt = datetime.strptime(from_time, "%H:%M:%S")
    to_dt = datetime.strptime(to_time, "%H:%M:%S")
    return from_dt <= current <= to_dt


def normalize_coordinates(lat: float, lng: float) -> Tuple[float, float]:
    """Normalize coordinates to 6 decimal places for Google Maps compatibility."""
    return (round(lat, 6), round(lng, 6))


def validate_coordinates(lat: Union[str, float], lng: Union[str, float]) -> Tuple[float, float]:
    """Validate and normalize coordinates for UK locations."""
    # Convert string coordinates to float, raise error if invalid
    try:
        lat_float = float(lat)
        lng_float = float(lng)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid coordinate format: lat={lat}, lng={lng}")
    
    # Global coordinate range validation
    if not (-90 <= lat_float <= 90):
        raise ValueError(f"Latitude {lat_float} must be between -90 and 90 degrees")
    
    if not (-180 <= lng_float <= 180):
        raise ValueError(f"Longitude {lng_float} must be between -180 and 180 degrees")
    
    # UK-specific bounds validation to catch obviously wrong coordinates
    # Covers mainland UK plus Northern Ireland and surrounding islands
    if not (49.5 <= lat_float <= 61.0):
        raise ValueError(f"Latitude {lat_float} is outside UK bounds")
        
    if not (-8.5 <= lng_float <= 2.0):
        raise ValueError(f"Longitude {lng_float} is outside UK bounds")
    
    return normalize_coordinates(lat_float, lng_float)


def calculate_travel_time(distance_miles: float, current_time: str) -> int:
    """Calculate travel time in minutes based on distance and London traffic conditions."""
    # Load London-specific speed configurations
    (distance_threshold_central, distance_threshold_urban, distance_threshold_outer,
     speed_central_london, speed_urban_london, speed_outer_london, speed_long_distance,
     peak_hours, peak_hour_speed_reduction) = import_config(
        'distance_threshold_central', 'distance_threshold_urban', 'distance_threshold_outer',
        'speed_central_london', 'speed_urban_london', 'speed_outer_london', 'speed_long_distance',
        'peak_hours', 'peak_hour_speed_reduction')
    
    # Select appropriate speed based on distance zones in London
    if distance_miles <= distance_threshold_central:
        base_speed_mph = speed_central_london  # Heavy congestion
    elif distance_miles <= distance_threshold_urban:
        base_speed_mph = speed_urban_london    # Moderate traffic
    elif distance_miles <= distance_threshold_outer:
        base_speed_mph = speed_outer_london    # Outer London
    else:
        base_speed_mph = speed_long_distance   # May include faster roads
    
    # Apply peak hour speed reduction if traveling during rush hour
    current_hour = current_time[:2] + ":00:00"
    speed_mph = base_speed_mph * peak_hour_speed_reduction if current_hour in peak_hours else base_speed_mph
    
    return int((distance_miles / speed_mph) * 60)
