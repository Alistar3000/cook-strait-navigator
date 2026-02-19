"""
Utility functions for location-aware mooring recommendations.
Includes geospatial calculations, coordinate extraction, and multi-day trip analysis.
"""

import re
import math
from typing import List, Tuple, Optional
from datetime import datetime, timedelta


def extract_location_coordinates(text: str) -> Optional[Tuple[float, float]]:
    """
    Extract coordinates from mooring location text.
    Looks for pattern: -41.XXXX, 174.XXXX (latitude, longitude)
    Returns: (latitude, longitude) tuple or None
    """
    # Pattern for coordinates: -41.1234, 174.5678
    pattern = r'-?\d+\.\d+,?\s*\d+\.\d+'
    match = re.search(pattern, text)
    
    if match:
        coord_str = match.group(0).replace(' ', '')
        try:
            lat, lon = coord_str.split(',')
            return (float(lat), float(lon))
        except (ValueError, IndexError):
            return None
    
    return None


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points on Earth using Haversine formula.
    Returns distance in nautical miles.
    """
    R = 3440.065  # Earth radius in nautical miles
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


def parse_location_zone(location_query: str) -> Tuple[Optional[Tuple[float, float]], str]:
    """
    Parse user's location input and return approximate coordinates.
    Recognizes key areas in QCS/Tory Channel region.
    
    Returns: ((lat, lon), zone_name) or (None, "unknown")
    """
    query_lower = location_query.lower().strip()
    
    # Define anchor points for major zones
    zones = {
        'tory channel': (-41.1433, 174.1767),
        'tory': (-41.1433, 174.1767),
        'ship cove': (-41.0583, 174.2372),
        'queen charlotte sound': (-41.15, 174.30),
        'qcs': (-41.15, 174.30),
        'outer sound': (-41.15, 174.20),
        'middle sound': (-41.15, 174.35),
        'inner sound': (-41.15, 174.45),
        'pelorus sound': (-41.30, 174.40),
        'pelorus': (-41.30, 174.40),
        'havelock': (-41.2833, 174.2667),
        'picton': (-41.2833, 174.0167),
        'port underwood': (-41.4167, 174.0833),
        'port': (-41.4167, 174.0833),
        'motuara': (-41.1100, 174.2900),
        'entrance': (-41.15, 174.10),
        'cape koamaru': (-41.3167, 173.9500),
    }
    
    for key, coords in zones.items():
        if key in query_lower:
            return coords, key
    
    return None, query_lower


def extract_trip_duration(query: str) -> Optional[int]:
    """
    Extract trip duration from user query.
    Looks for patterns like "3 day trip", "weekend", "overnight", etc.
    
    Returns: number of days or None if not detected
    """
    query_lower = query.lower()
    
    # Check for explicit day counts
    match = re.search(r'(\d+)\s*(?:day|night)', query_lower)
    if match:
        days = int(match.group(1))
        # If nights specified, convert to days (n nights = n+1 days)
        if 'night' in query_lower[match.start():match.end()]:
            days = days + 1
        return days
    
    # Check for weekend (assume 2-3 days)
    if 'weekend' in query_lower:
        return 3
    
    # Check for overnight/night
    if 'overnight' in query_lower or 'one night' in query_lower:
        return 2
    
    # Check for week
    if 'week' in query_lower:
        return 7
    
    return None


def get_weather_for_trip_duration(weather_data: dict, num_days: int) -> dict:
    """
    Extract weather data for the entire trip duration.
    Weather data should contain forecast for multiple days.
    
    Returns: Weather dict with day-by-day analysis
    """
    if not weather_data or 'forecast' not in weather_data:
        return weather_data
    
    # This will be populated with actual forecast data structure
    # For now, return the data as-is
    return weather_data


def filter_moorings_by_distance(
    moorings: List[dict],
    user_position: Tuple[float, float],
    max_distance_nm: float = 15.0
) -> List[Tuple[dict, float]]:
    """
    Filter moorings by distance from user's position.
    Returns list of (mooring_dict, distance_nm) sorted by distance.
    
    Args:
        moorings: List of mooring location dicts with 'coordinates' key
        user_position: (latitude, longitude) tuple
        max_distance_nm: Maximum distance in nautical miles
    
    Returns: List of (mooring, distance) tuples sorted by distance
    """
    if not user_position:
        return [(m, None) for m in moorings]
    
    nearby = []
    for mooring in moorings:
        if 'coordinates' not in mooring or not mooring['coordinates']:
            continue
        
        lat, lon = mooring['coordinates']
        distance = haversine_distance(
            user_position[0], user_position[1],
            lat, lon
        )
        
        if distance <= max_distance_nm:
            nearby.append((mooring, distance))
    
    # Sort by distance
    nearby.sort(key=lambda x: x[1])
    return nearby


def analyze_mooring_for_weather(
    mooring: dict,
    wind_direction: str,
    wind_speed: float,
    wave_height: float,
    num_days: int = 1
) -> dict:
    """
    Analyze if a mooring is suitable for given weather conditions.
    For multi-day trips, considers wind changes.
    
    Returns: Suitability analysis dict
    """
    analysis = {
        'name': mooring.get('name', 'Unknown'),
        'suitable': False,
        'shelter_rating': 'Unknown',
        'concerns': [],
        'notes': []
    }
    
    # Extract shelter info from mooring description
    description = mooring.get('description', '').lower()
    content = mooring.get('content', '').lower()
    full_text = description + ' ' + content
    
    # Simple shelter evaluation based on wind direction
    # This should be enhanced based on actual shelter data
    wind_dir_lower = wind_direction.lower()
    
    if f'shelter{wind_dir_lower}' in full_text or f'{wind_dir_lower}' in full_text:
        analysis['shelter_rating'] = 'Good'
        analysis['suitable'] = True
    else:
        # Default analysis if specific shelter not mentioned
        if 'exposed' in full_text:
            analysis['shelter_rating'] = 'Exposed'
            analysis['suitable'] = False
        elif 'shelter' in full_text:
            analysis['shelter_rating'] = 'Moderate'
            analysis['suitable'] = True
    
    # Wave concerns
    if wave_height > 1.5 and 'swell' in full_text:
        analysis['concerns'].append(f"Swell sensitivity - bay collects significant swell")
    
    # Multi-day trip notes
    if num_days > 1:
        analysis['notes'].append(f"Good for {num_days}-day stay")
    
    return analysis


def generate_multiday_mooring_strategy(
    moorings_suitability: List[dict],
    forecast_days: List[dict],
    num_days: int
) -> str:
    """
    Generate a multi-day mooring strategy considering weather changes over the trip.
    
    Args:
        moorings_suitability: List of mooring analysis dicts
        forecast_days: List of weather forecasts for each day
        num_days: Total trip duration
    
    Returns: Strategy text describing recommended mooring movements
    """
    if not moorings_suitability:
        return "No suitable moorings found for specified duration and conditions."
    
    strategy = f"🛥️ **{num_days}-DAY TRIP MOORING STRATEGY**\n\n"
    
    # Sort by suitability
    suitable = [m for m in moorings_suitability if m['suitable']]
    
    if not suitable:
        return strategy + "⚠️ Limited suitable moorings for these conditions. Consider alternative locations."
    
    # For now, recommend top options
    strategy += "**Recommended Anchorages (by proximity & suitability):**\n\n"
    for i, mooring in enumerate(suitable[:3], 1):
        strategy += f"{i}. **{mooring['name']}** - {mooring['shelter_rating']} shelter\n"
        if mooring.get('distance'):
            strategy += f"   Distance: {mooring['distance']:.1f}nm\n"
        if mooring['concerns']:
            strategy += f"   ⚠️ {', '.join(mooring['concerns'])}\n"
        strategy += "\n"
    
    return strategy
