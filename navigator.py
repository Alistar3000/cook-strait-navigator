import os
import requests
import urllib3
import warnings
import time
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv

from duckduckgo_search import DDGS
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.agents import Tool, create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from mooring_utils import (
    extract_location_coordinates,
    parse_location_zone,
    extract_trip_duration,
    filter_moorings_by_distance,
    analyze_mooring_for_weather,
    generate_multiday_mooring_strategy
)
# Import bite times API
try:
    from bite_times_api import get_bite_times_for_agent
except ImportError:
    # Fallback if bite_times_api not available
    def get_bite_times_for_agent(location="wellington", days=3):
        return "Bite times API not available. Check https://www.fishing.net.nz/fishing-advice/bite-times/"

# Try to import streamlit for Streamlit Cloud secrets support
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

# Suppress warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()

# --- API RATE LIMITING & QUOTA PROTECTION ---
# Track requests to prevent abuse and quota exhaustion
API_REQUEST_LIMITER = {
    'metocean': {'last_request': 0, 'min_interval': 2.0},  # Min 2 sec between requests
    'niwa': {'last_request': 0, 'min_interval': 1.0},      # Min 1 sec between requests
    'openai': {'request_count': 0, 'limit_per_hour': 20}   # Max 20 requests/hour
}
REQUEST_TIMESTAMPS = []  # Track all requests for hourly rate limiting

def check_rate_limit(api_name):
    """Check if we should throttle the request to protect API quotas.
    
    Returns:
        (allowed: bool, message: str or None)
    """
    global API_REQUEST_LIMITER, REQUEST_TIMESTAMPS
    
    now = time.time()
    
    # Clean up old timestamps (>1 hour)
    REQUEST_TIMESTAMPS = [ts for ts in REQUEST_TIMESTAMPS if now - ts < 3600]
    
    if api_name in ['metocean', 'niwa']:
        # Min interval throttling
        limiter = API_REQUEST_LIMITER[api_name]
        time_since_last = now - limiter['last_request']
        
        if time_since_last < limiter['min_interval']:
            wait_time = limiter['min_interval'] - time_since_last
            return False, f"⏳ Rate limited (wait {wait_time:.1f}s). Too many rapid requests."
        
        limiter['last_request'] = now
        return True, None
    
    elif api_name == 'openai':
        # Hourly quota limiting
        if len(REQUEST_TIMESTAMPS) >= API_REQUEST_LIMITER['openai']['limit_per_hour']:
            return False, (f"⚠️ **Quota Alert:** You've made {len(REQUEST_TIMESTAMPS)} requests in the last hour. "
                          f"Please wait a moment before making more requests to avoid consuming tokens.")
        
        REQUEST_TIMESTAMPS.append(now)
        return True, None
    
    return True, None

def get_secret(key_name):
    """Get a secret from Streamlit Cloud or local .env file.
    
    Args:
        key_name: Name of the secret (e.g., 'METOCEAN_API_KEY')
        
    Returns:
        The secret value or None if not found
    """
    # Try Streamlit secrets first (for Streamlit Cloud)
    if STREAMLIT_AVAILABLE:
        try:
            return st.secrets.get(key_name)
        except (FileNotFoundError, KeyError, AttributeError):
            pass
    
    # Fallback to environment variable (for local development)
    return os.getenv(key_name)

# --- 1. COMPREHENSIVE LOCATION DATABASE ---
LOCATIONS = {
    # Wellington / North Island Side
    "mana marina": {"lat": -41.10108, "lon": 174.86700},
    "mana": {"lat": -41.1141, "lon": 174.8512},
    "plimmerton": {"lat": -41.0821, "lon": 174.8615},
    "pukerua bay": {"lat": -41.0312, "lon": 174.8945},
    "titahi bay": {"lat": -41.1023, "lon": 174.8312},
    "makara": {"lat": -41.2245, "lon": 174.7123},
    "karori rock": {"lat": -41.3482, "lon": 174.6523},
    "terawhiti": {"lat": -41.2912, "lon": 174.6154},
    "sinclair head": {"lat": -41.3610, "lon": 174.7670},
    "barrett reef": {"lat": -41.3520, "lon": 174.8350},
    
    # Cook Strait Center / Hazards
    "cook strait": {"lat": -41.2000, "lon": 174.5500},
    "78m rise": {"lat": -41.2000, "lon": 174.5500},
    "fishermans rock": {"lat": -41.0672, "lon": 174.6015},
    "hunter bank": {"lat": -40.9671, "lon": 174.8172},
    "awash rock": {"lat": -41.1415, "lon": 174.3750},
    "cook rock": {"lat": -41.0330, "lon": 174.4670},
    
    # Marlborough Sounds / South Island Side
    "tory channel": {"lat": -41.2145, "lon": 174.3212},
    "tory": {"lat": -41.2145, "lon": 174.3212},  # Short form
    "cape koamaru": {"lat": -41.0883, "lon": 174.3814},
    "koamaru": {"lat": -41.0883, "lon": 174.3814},  # Short form
    "brothers islands": {"lat": -41.1020, "lon": 174.4410},
    "ship cove": {"lat": -41.0950, "lon": 174.2420},
    "motuara island": {"lat": -41.0500, "lon": 174.2700},
    "perano head": {"lat": -41.1830, "lon": 174.3160}
}

# Cook Strait Tide Knowledge - Compass directions for flood (rising) and ebb (falling) tides
# These are generalized patterns; actual tides vary with specific entrances and times
TIDE_DIRECTIONS = {
    # Flood tide (incoming, water level rising) flows generally northeast
    "flood": {
        "primary": 45,      # degrees (NE)
        "range": (0, 90),   # N to E
        "description": "Flood tide flows northeast into the strait"
    },
    # Ebb tide (outgoing, water level falling) flows generally southwest  
    "ebb": {
        "primary": 225,     # degrees (SW)
        "range": (180, 270), # S to W
        "description": "Ebb tide flows southwest out of the strait"
    },
    # Rising water level
    "rising": {
        "primary": 45,
        "range": (0, 90),
        "description": "Rising tide flows northeast"
    },
    # Falling water level
    "falling": {
        "primary": 225,
        "range": (180, 270),
        "description": "Falling tide flows southwest"
    }
}

# Fishing Location Characteristics - metadata for location recommendations
LOCATION_CHARACTERISTICS = {
    # North Island - Wellington
    "mana marina": {"difficulty": 1, "shelter": "High", "type": "Marina", "protected": True, "best_wind": 15, "best_wave": 0.8},
    "mana": {"difficulty": 1, "shelter": "High", "type": "Beach/Estuary", "protected": True, "best_wind": 15, "best_wave": 0.8},
    "plimmerton": {"difficulty": 2, "shelter": "Medium", "type": "Beach", "protected": True, "best_wind": 18, "best_wave": 1.2},
    "pukerua bay": {"difficulty": 2, "shelter": "Medium", "type": "Beach", "protected": False, "best_wind": 20, "best_wave": 1.5},
    "titahi bay": {"difficulty": 1, "shelter": "High", "type": "Bay", "protected": True, "best_wind": 15, "best_wave": 0.9},
    "makara": {"difficulty": 3, "shelter": "Low", "type": "Exposed Beach", "protected": False, "best_wind": 12, "best_wave": 1.0},
    "karori rock": {"difficulty": 4, "shelter": "Very Low", "type": "Open Water", "protected": False, "best_wind": 10, "best_wave": 0.8},
    "terawhiti": {"difficulty": 4, "shelter": "Very Low", "type": "Exposed", "protected": False, "best_wind": 8, "best_wave": 0.5},
    
    # Sounds - South Island
    "tory channel": {"difficulty": 3, "shelter": "Medium", "type": "Channel", "protected": True, "best_wind": 18, "best_wave": 1.3},
    "cape koamaru": {"difficulty": 3, "shelter": "Low", "type": "Headland", "protected": False, "best_wind": 15, "best_wave": 1.1},
    "ship cove": {"difficulty": 2, "shelter": "Medium", "type": "Cove", "protected": True, "best_wind": 16, "best_wave": 1.0},
    "motuara island": {"difficulty": 2, "shelter": "Medium", "type": "Island", "protected": False, "best_wind": 16, "best_wave": 1.2},
}

def get_location_recommendation_score(location_name, wind_kt, wave_m, boat_class, tide_state=None):
    """Score a location based on current/forecast weather conditions.
    
    Args:
        location_name: Name of the location
        wind_kt: Wind speed in knots
        wave_m: Wave height in meters
        boat_class: Boat class (SMALL, MEDIUM, LARGE)
        tide_state: Optional tide state (rising/falling/flood/ebb)
        
    Returns:
        dict with score (0-100), reason, and recommendation
    """
    if location_name not in LOCATION_CHARACTERISTICS:
        return {"score": 50, "reason": "Unknown location"}
    
    loc = LOCATION_CHARACTERISTICS[location_name]
    score = 100
    issues = []
    positives = []
    
    # Set thresholds based on boat class and location difficulty
    if boat_class == "SMALL":
        # Small boats need calmer conditions
        if loc["difficulty"] >= 3:
            score -= 20
            issues.append(f"Location too exposed for small boat")
    elif boat_class == "MEDIUM":
        if loc["difficulty"] >= 4:
            score -= 15
            issues.append("Location exposed for medium boat")
    # LARGE boats can handle more
    
    # Wind scoring
    best_wind = loc["best_wind"]
    if wind_kt <= best_wind - 5:
        positives.append("Light winds - ideal conditions")
        score += 10
    elif wind_kt <= best_wind:
        positives.append("Good wind conditions")
        score += 5
    elif wind_kt <= best_wind + 5:
        score -= 5
        issues.append(f"Wind slightly above ideal ({wind_kt:.0f}kt vs {best_wind}kt)")
    elif wind_kt <= best_wind + 10:
        score -= 15
        issues.append(f"Wind moderately above ideal")
    else:
        score -= 30
        issues.append(f"Wind too strong for safe fishing")
    
    # Wave scoring
    best_wave = loc["best_wave"]
    if wave_m <= best_wave - 0.3:
        positives.append("Calm seas")
        score += 10
    elif wave_m <= best_wave:
        positives.append("Wave height good")
        score += 5
    elif wave_m <= best_wave + 0.3:
        score -= 5
        issues.append(f"Waves slightly choppy")
    elif wave_m <= best_wave + 0.6:
        score -= 15
        issues.append("Waves moderately choppy")
    else:
        score -= 25
        issues.append("Seas too rough for safe fishing")
    
    # Shelter bonus for protected locations
    if loc["protected"] and wind_kt > 18:
        positives.append(f"Protected location helps in moderate wind")
        score += 8
    
    # Tide condition bonus
    if tide_state in ["rising", "flood"]:
        positives.append("Rising tide - good for fishing")
        score += 5
    elif tide_state in ["falling", "ebb"]:
        issues.append("Falling tide may reduce activity")
        score -= 3
    
    # Clamp score between 0-100
    score = max(0, min(100, score))
    
    reason = ""
    if positives:
        reason = ", ".join(positives)
    if issues:
        reason += (" | " if reason else "") + " ⚠️ ".join(issues)
    if not reason:
        reason = "Average conditions"
    
    return {
        "score": score,
        "location": location_name,
        "conditions": f"{wind_kt:.0f}kt wind, {wave_m:.1f}m waves",
        "reason": reason,
        "type": loc["type"],
        "shelter": loc["shelter"]
    }

def recommend_fishing_locations(wind_data, wave_data, boat_class, boat_size, tide_state=None, tide_info=None, num_recommendations=3):
    """Recommend best fishing locations based on weather forecast.
    
    Args:
        wind_data: List of wind speeds (knots) forecasted
        wave_data: List of wave heights (meters) forecasted  
        boat_class: Boat class (SMALL, MEDIUM, LARGE)
        boat_size: Boat size in meters
        tide_state: Optional current tide state
        tide_info: Optional tide info dict from NIWA
        num_recommendations: Number of recommendations to return
        
    Returns:
        str with formatted location recommendations
    """
    if not wind_data or not wave_data:
        return ""
    
    # Use average conditions from forecast (typically first 3 time points)
    avg_wind = sum(wind_data[:3]) / len(wind_data[:3]) if wind_data else 0
    avg_wave = sum(wave_data[:3]) / len(wave_data[:3]) if wave_data else 0
    
    # Get tide info for recommendations
    effective_tide = tide_state
    if not effective_tide and tide_info and 'tide_state' in tide_info:
        effective_tide = tide_info['tide_state']
    
    # Score all fishing locations
    scores = []
    for location_name in LOCATION_CHARACTERISTICS.keys():
        result = get_location_recommendation_score(
            location_name, avg_wind, avg_wave, boat_class, effective_tide
        )
        scores.append(result)
    
    # Sort by score (highest first)
    scores.sort(key=lambda x: x["score"], reverse=True)
    
    # Filter, recommendations - only suggest if score is decent (>40)
    good_locations = [s for s in scores if s["score"] > 40]
    
    if not good_locations:
        return "\n🎣 **Location Status:** Current conditions challenging for fishing - consider waiting or checking calmer bays (Mana, Titahi}\n"
    
    # Format recommendations
    recommendation_text = "\n🎣 **Recommended Fishing Locations:**\n"
    
    for i, loc in enumerate(good_locations[:num_recommendations], 1):
        score_emoji = "🟢" if loc["score"] > 75 else "🟡" if loc["score"] > 55 else "🟠"
        recommendation_text += f"{i}. {score_emoji} **{loc['location'].title()}** ({loc['shelter']} shelter, {loc['type']})\n"
        recommendation_text += f"   Score: {loc['score']:.0f}/100 | {loc['conditions']}\n"
        recommendation_text += f"   {loc['reason']}\n"
    
    return recommendation_text

def fetch_niwa_tide_data(lat, lon, days=2):
    """Fetch tide data from NIWA Tide API.
    
    Args:
        lat: Latitude
        lon: Longitude
        days: Number of days to forecast
        
    Returns:
        dict with tide_state, magnitude_factor, description, and raw_data
    """
    try:
        # CHECK RATE LIMITING BEFORE MAKING REQUEST
        allowed, _ = check_rate_limit('niwa')
        if not allowed:
            return None
        
        api_key = get_secret("NIWA_API_KEY")
        if not api_key:
            return None
        
        # NIWA Tide API endpoint - https://developer.niwa.co.nz/docs/tide-api/1/routes/data/get
        url = "https://api.niwa.co.nz/tides/data"
        
        # Note: NIWA uses 'long' not 'lon', and numberOfDays parameter
        params = {
            "lat": lat,
            "long": lon,  # IMPORTANT: 'long' not 'lon'
            "numberOfDays": min(days, 31),  # Max 31 days
            "apikey": api_key  # Direct query parameter
        }
        
        r = requests.get(url, params=params, timeout=5, verify=False)
        
        if r.status_code != 200:
            return None
        
        data = r.json()
        
        # Parse tide heights to determine state and magnitude
        if "values" not in data or not data["values"]:
            return None
        
        values = data["values"]
        
        # Extract tide heights from NIWA response
        heights = []
        for value in values:
            try:
                height = float(value.get("value", 0))
                heights.append(height)
            except (ValueError, TypeError):
                pass
        
        if len(heights) < 2:
            return None
        
        # Determine if tide is rising or falling (compare first few points)
        tide_trend = "rising" if heights[1] > heights[0] else "falling"
        
        # Calculate tide range for magnitude (spring vs neap)
        tide_min = min(heights)
        tide_max = max(heights)
        tide_range = tide_max - tide_min
        
        # Magnitude factor: spring tide (large range) vs neap tide (small range)
        # Cook Strait typical range: ~1.5m average, 1.0-2.0m varies
        if tide_range > 1.5:
            magnitude = "SPRING"  # Large tidal range
            magnitude_factor = 1.5  # 50% increase in chop
        elif tide_range < 0.9:
            magnitude = "NEAP"    # Small tidal range
            magnitude_factor = 0.7  # 30% decrease in chop
        else:
            magnitude = "NORMAL"
            magnitude_factor = 1.0
        
        result = {
            "tide_state": tide_trend,
            "magnitude": magnitude,
            "magnitude_factor": magnitude_factor,
            "range": tide_range,
            "description": f"{magnitude} tide ({tide_trend.upper()}): range {tide_range:.2f}m",
            "raw_heights": heights[:20]
        }
        
        return result
        
    except requests.exceptions.Timeout:
        return None
    except Exception as e:
        return None

def fetch_marine_data(location_input, days=2):
    """MetOcean v2 fetcher with DETAILED error logging.
    
    Args:
        location_input: Location name or query (may include vessel info context)
        days: Number of days to forecast (default 2, max 10)
    """
    # Extract boat_size from context if present (format: "Vessel: 6.5m. ...")
    boat_size = 6.0  # default 6m (medium boat)
    if "Vessel:" in location_input:
        try:
            vessel_part = location_input.split("Vessel:")[1].split("m")[0]
            boat_size = float(vessel_part.strip())
        except:
            pass
    
    # Detect tide state from user input (flood, ebb, rising, falling)
    tide_state = None
    query_lower = str(location_input).lower()
    for state in ["flood", "rising", "ebb", "falling"]:
        if state in query_lower:
            tide_state = state
            break
    
    try:
        api_key = get_secret("METOCEAN_API_KEY")
        
        if not api_key:
            return "❌ ERROR: METOCEAN_API_KEY not found (check Streamlit Secrets)"
        
        query = str(location_input).lower().strip()
        
        # Limit days to reasonable range (marine forecasts beyond 10 days are unreliable)
        days = max(1, min(int(days), 10))
        
        # "The Sounds" DETECTION AND ENTRANCE RECOGNITION
        coords = None
        location_name = query
        
        # First, check if user is specifying an entrance directly (even without "sounds" keyword)
        # This handles follow-up answers like "Tory Channel", "Tory", "Koamaru", or "Cape Koamaru"
        has_tory = any(word in query for word in ["tory", "eastern", "east entrance", "east", "tory channel"])
        has_koamaru = any(word in query for word in ["koamaru", "northern", "north entrance", "northwest", "north", "cape koamaru"])
        
        # If it's just an entrance name without location context, treat it as that entrance
        if has_tory and not coords:
            coords = LOCATIONS["tory channel"]
            location_name = "Tory Channel (Eastern Entrance)"
        if has_tory and not coords:
            coords = LOCATIONS["tory channel"]
            location_name = "Tory Channel (Eastern Entrance)"
        elif has_koamaru and not coords:
            coords = LOCATIONS["cape koamaru"]
            location_name = "Cape Koamaru (Northern Entrance)"
        
        # If user mentions "cross" or "crossing" the Strait, treat as Sounds crossing
        if not coords and any(word in query for word in ["cross", "crossing", "cross the strait"]):
            return ("⚠️ CLARIFICATION NEEDED:\n\n"
                   "To cross the Cook Strait, which entrance will you use?\n\n"
                   "1️⃣ TORY CHANNEL (Eastern) - or just say \"Tory\"\n"
                   "2️⃣ CAPE KOAMARU (Northern) - or just say \"Koamaru\"\n\n"
                   "❓ Which entrance will you be crossing to?")
        
        # If user mentions "sounds" or "marlborough" but hasn't specified entrance, ask for clarification
        if not coords and ("sounds" in query or "marlborough" in query):
            return ("⚠️ CLARIFICATION NEEDED:\n\n"
                   "The Marlborough Sounds has TWO main entrances:\n\n"
                   "1️⃣ TORY CHANNEL (Eastern) - or just say \"Tory\"\n"
                   "2️⃣ CAPE KOAMARU (Northern) - or just say \"Koamaru\"\n\n"
                   "❓ Which entrance will you use?")
        
        # Location lookup
        if not coords:
            clean_query = query.replace(" ", "")
            
            if clean_query in LOCATIONS:
                coords = LOCATIONS[clean_query]
                location_name = query.title()
            else:
                for key, val in LOCATIONS.items():
                    if key in query or query in key:
                        coords = val
                        location_name = key.title()
                        break
            
            if not coords:
                coords = LOCATIONS["cook strait"]
                location_name = "Cook Strait (Central)"
        
        now_dt = datetime.now()
        
        # CHECK RATE LIMITING BEFORE MAKING REQUEST
        allowed, limit_msg = check_rate_limit('metocean')
        if not allowed:
            return limit_msg
        
        # API PARAMETERS - Enhanced with wind direction (MetOcean doesn't provide tide.direction/level)
        params = {
            "lat": coords['lat'],
            "lon": coords['lon'],
            "variables": "wind.speed.at-10m,wind.direction.at-10m,wave.height",
            "from": now_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "to": (now_dt + timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        
        url = "https://forecast-v2.metoceanapi.com/point/time"
        
        # Add user-agent to identify this tool and track usage
        headers = {
            "x-api-key": api_key,
            "User-Agent": "CookStraitNavigator/1.0 (Marine Safety Tool)"
        }
        
        r = requests.get(url, params=params, headers=headers, verify=False, timeout=15)
        
        if r.status_code != 200:
            error_text = r.text[:300]
            return (f"⚠️ Weather API error {r.status_code}.\n"
                   f"Error: {error_text}\n\n"
                   f"Use WebConsensus to check weather sites.")
        
        data = r.json()
        
        # Fetch NIWA tide data
        niwa_tide = fetch_niwa_tide_data(coords['lat'], coords['lon'], days=days)
        tide_magnitude_factor = niwa_tide['magnitude_factor'] if niwa_tide else 1.0
        tide_info_str = niwa_tide['description'] if niwa_tide else "Tide data unavailable"
        
                
        if not isinstance(data, dict):
            return "⚠️ Invalid data format."

        variables = data.get('variables', {})
        time_dim = data.get('dimensions', {}).get('time', {})
        
        # FIXED: Handle times - could be dict with 'data' key or a list
        if isinstance(time_dim, dict):
            times = time_dim.get('data', [])
        else:
            times = time_dim if isinstance(time_dim, list) else []
        
        wind = variables.get('wind.speed.at-10m', {}).get('data', [])
        wind_dir = variables.get('wind.direction.at-10m', {}).get('data', [])
        wave = variables.get('wave.height', {}).get('data', [])

        if not wind or not wave:
            return f"⚠️ No forecast data for {location_name}."
        
        # Build report
        report = f"═══ {location_name.upper()} ═══\n"
        report += f"📍 {coords['lat']:.3f}°S, {coords['lon']:.3f}°E\n"
        report += f"📅 Forecast: {days} day(s)\n\n"
        
        # Determine max entries based on days requested
        # Show more data for multi-day analysis
        if days <= 2:
            max_display = 16
        elif days <= 4:
            max_display = 32
        elif days <= 7:
            max_display = 56  # ~8 per day
        else:
            max_display = 80  # ~8 per day for up to 10 days
        
        max_entries = min(len(wind), len(wave), max_display)
        
        # Track opposition across ALL forecast periods
        opposition_events = []  # List of (index, time, wind_dir, opposition_factor)
        opposition_periods = []  # List of time strings when opposition occurs
        period_analyses = []  # Detailed analysis for each period
        
        for i in range(max_entries):
            w_kts = wind[i] * 1.944  # m/s to knots
            wv_m = wave[i]
            
            # Get wind direction if available
            w_dir = wind_dir[i] if i < len(wind_dir) else None
            
            # Detect wind vs tide opposition using available tide data
            opposition_note = ""
            opposition_has_occurred = False
            opposition_factor = 1.0
            
            # Determine tide state: use user input OR NIWA data
            effective_tide_state = tide_state
            if not effective_tide_state and niwa_tide and 'tide_state' in niwa_tide:
                effective_tide_state = niwa_tide['tide_state']  # 'rising' or 'falling' from NIWA
            
            if effective_tide_state and w_dir is not None:
                # Get expected tide direction from local knowledge
                tide_info = TIDE_DIRECTIONS.get(effective_tide_state)
                if tide_info:
                    tide_min, tide_max = tide_info["range"]
                    
                    # Check if wind is roughly opposite to tide flow
                    # Wind opposes tide if it's within 45° of opposite direction
                    tide_primary = tide_info["primary"]
                    opposite_dir = (tide_primary + 180) % 360
                    
                    # Calculate angle difference (circular)
                    diff = abs(w_dir - opposite_dir)
                    if diff > 180:
                        diff = 360 - diff
                    
                    # Map wind direction to compass point
                    compass_pts = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
                    compass_idx = int((w_dir + 11.25) / 22.5) % 16
                    wind_compass = compass_pts[compass_idx]
                    
                    tide_direction_name = "Flood (NE)" if effective_tide_state in ["flood", "rising"] else "Ebb (SW)"
                    
                    if diff < 45:  # Wind is within 45° of directly opposing tide
                        opposition_factor = 1.4  # 40% increase in chop
                        opposition_note = f" ⚠️ OPPOSES TIDE - Steep seas!"
                        opposition_has_occurred = True
                        
                        # Get time for this period
                        if i < len(times):
                            time_str = times[i]
                            try:
                                if isinstance(time_str, str):
                                    dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                                    time_display = dt.strftime('%a %d %H:%M')
                                else:
                                    time_display = str(time_str)[:16]
                            except:
                                time_display = f"T+{i*3}h"
                        else:
                            time_display = f"T+{i*3}h"
                        
                        # Check for choppy water potential: tide range > 50cm AND wind > 7kt AND opposition
                        tide_range = niwa_tide.get('range', 0) if niwa_tide else 0
                        is_choppy_potential = tide_range > 0.5 and w_kts > 7
                        
                        opposition_events.append({
                            'index': i,
                            'time': time_display,
                            'wind_dir': w_dir,
                            'wind_compass': wind_compass,
                            'tide_dir': tide_direction_name,
                            'angle_diff': diff,
                            'wind_kt': w_kts,
                            'wave_m': wv_m,
                            'tide_range': tide_range,
                            'choppy_potential': is_choppy_potential  # Flagged for choppy water
                        })
            
            # Boat-size adjusted thresholds
            if boat_size < 6.0:
                # Small boats (< 6m): conservative thresholds
                danger_wind = 25
                nogo_wind = 18
                caution_wind = 14
                danger_wave = 1.8
                nogo_wave = 1.3
                caution_wave = 0.8
                boat_class = "SMALL"
            elif boat_size < 9.0:
                # Medium boats (6-9m): standard thresholds
                danger_wind = 28
                nogo_wind = 20
                caution_wind = 15
                danger_wave = 2.2
                nogo_wave = 1.5
                caution_wave = 1.0
                boat_class = "MEDIUM"
            else:
                # Large boats (9m+): more tolerant thresholds
                danger_wind = 32
                nogo_wind = 24
                caution_wind = 18
                danger_wave = 2.5
                nogo_wave = 1.8
                caution_wave = 1.2
                boat_class = "LARGE"
            
            # Effective wave height accounting for opposition and tide magnitude
            # Combine: wind opposition (1.4x) × NIWA tide magnitude factor (0.7-1.5x)
            effective_wave = wv_m * opposition_factor * tide_magnitude_factor
            
            # Safety assessment with boat-size specific thresholds
            if w_kts > danger_wind or effective_wave > danger_wave:
                flag = " 🔴 DANGER"
            elif w_kts > nogo_wind or effective_wave > nogo_wave:
                flag = " 🟠 NO-GO"
            elif w_kts > caution_wind or effective_wave > caution_wave:
                flag = " 🟡 CAUTION"
            else:
                flag = " ✅ SAFE"
            
            # Time formatting
            if i < len(times):
                time_str = times[i]
                try:
                    if isinstance(time_str, str):
                        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                        time_display = dt.strftime('%a %d %H:%M')
                    else:
                        time_display = str(time_str)[:16]
                except:
                    time_display = f"T+{i*3}h"
            else:
                time_display = f"T+{i*3}h"
            
            # Build forecast line with wind direction if available
            direction_str = ""
            if w_dir is not None:
                direction_str = f" {int(w_dir)}°"
            
            report += f"[{time_display}] Wind: {w_kts:.0f}kt{direction_str} | Wave: {wv_m:.1f}m{flag}{opposition_note}\n"
        
        # Build comprehensive opposition summary from ALL periods
        opposition_summary = ""
        choppy_potential_count = 0
        
        if opposition_events:
            opposition_summary = f"\n🌊 **WIND/TIDE OPPOSITION ANALYSIS:**\n"
            opposition_summary += f"   Opposition detected in {len(opposition_events)} period(s):\n\n"
            
            # Separate events by choppy water potential
            choppy_events = [e for e in opposition_events if e['choppy_potential']]
            normal_opposition = [e for e in opposition_events if not e['choppy_potential']]
            
            # Highlight choppy water potential first
            if choppy_events:
                choppy_potential_count = len(choppy_events)
                opposition_summary += f"   🚨 **CHOPPY WATER POTENTIAL** (Tide > 50cm + Wind > 7kt + Opposition):\n\n"
                for opp in choppy_events:
                    opposition_summary += (f"   • [{opp['time']}] ⚠️ CRITICAL CONDITIONS\n"
                                          f"      Wind: {opp['wind_dir']:.0f}° ({opp['wind_compass']}) opposes {opp['tide_dir']}\n"
                                          f"      Tide range: {opp['tide_range']:.2f}m | Wind: {opp['wind_kt']:.0f}kt | Wave: {opp['wave_m']:.1f}m\n"
                                          f"      Angle diff: {opp['angle_diff']:.0f}° | Effect: Steep, choppy seas (40% chop increase)\n\n")
            
            # List normal opposition for reference
            if normal_opposition:
                opposition_summary += f"   Standard opposition (tide ≤ 50cm or wind ≤ 7kt):\n\n"
                for opp in normal_opposition:
                    opposition_summary += (f"   • [{opp['time']}] Wind {opp['wind_dir']:.0f}° ({opp['wind_compass']}) opposes {opp['tide_dir']}\n"
                                          f"      Tide: {opp['tide_range']:.2f}m | Wind: {opp['wind_kt']:.0f}kt | Wave: {opp['wave_m']:.1f}m\n"
                                          f"      Angle: {opp['angle_diff']:.0f}° | Effect: Increased chop (40% multiplier)\n\n")
            
            opposition_summary += f"   **Summary:** Wind against tide increases effective wave height by ~40%\n"
            if choppy_potential_count > 0:
                opposition_summary += f"   ⚠️ **{choppy_potential_count} period(s) with CHOPPY WATER POTENTIAL** - Conditions to avoid\n"
        
        if opposition_summary:
            report = opposition_summary + "\n" + report
        
        report += f"\n📏 **Vessel Class: {boat_class}** ({boat_size:.1f}m)\n"
        report += f"🚨 Safety Thresholds:\n"
        report += f"   • DANGER: Wind >{danger_wind}kt or Wave >{danger_wave:.1f}m\n"
        report += f"   • NO-GO: Wind >{nogo_wind}kt or Wave >{nogo_wave:.1f}m\n"
        report += f"   • CAUTION: Wind >{caution_wind}kt or Wave >{caution_wave:.1f}m\n"
        
        if tide_state:
            tide_info = TIDE_DIRECTIONS.get(tide_state)
            report += f"\n🌊 **Tide State: {tide_state.upper()}**\n"
            report += f"   {tide_info['description']}\n"
            report += f"   Opposition factor: 40% increase in effective wave chop\n"
        else:
            if niwa_tide:
                report += f"\n🌊 **Tide State: Auto-detected from NIWA data**\n"
                # Tide state will be shown in opposition_summary if NIWA data is available
            else:
                report += f"\n🌊 **Tide State: Not specified** (mention 'flood', 'ebb', 'rising', or 'falling' for analysis)\n"
        
        # Add NIWA tide magnitude info
        if niwa_tide:
            report += f"\n🌊 **NIWA Tide Data:**\n"
            report += f"   {niwa_tide['description']}\n"
            report += f"   Magnitude multiplier: {niwa_tide['magnitude_factor']:.1f}x\n"
            if niwa_tide['magnitude'] == "SPRING":
                report += f"   ⚠️ **Spring tide: More chop and current**\n"
            elif niwa_tide['magnitude'] == "NEAP":
                report += f"   ✅ **Neap tide: Calmer conditions**\n"
        
        report += f"\n💡 **Wind directions shown (0°=N, 90°=E, 180°=S, 270°=W)**\n"
        
        # Add weather pattern analysis from boating guides
        if wind and wind_dir:
            avg_wind = sum(wind[:3]) / len(wind[:3]) if wind else 0
            avg_wind_dir = sum(wind_dir[:3]) / len(wind_dir[:3]) if wind_dir else 0
            
            pattern_analysis = analyze_weather_patterns(
                wind_speed_kt=avg_wind,
                wind_direction=avg_wind_dir,
                tide_state=tide_state,
                location=location_name,
                boat_size=boat_size
            )
            if pattern_analysis:
                report += f"\n{pattern_analysis}"
        
        report += f"\n📏 **Vessel Class: {boat_class}** ({boat_size:.1f}m)\n"
        report += f"🚨 Safety Thresholds:\n"
        report += f"   • DANGER: Wind >{danger_wind}kt or Wave >{danger_wave:.1f}m\n"
        report += f"   • NO-GO: Wind >{nogo_wind}kt or Wave >{nogo_wave:.1f}m\n"
        report += f"   • CAUTION: Wind >{caution_wind}kt or Wave >{caution_wave:.1f}m\n"
        
        if tide_state:
            tide_info = TIDE_DIRECTIONS.get(tide_state)
            report += f"\n🌊 **Tide State: {tide_state.upper()}**\n"
            report += f"   {tide_info['description']}\n"
            report += f"   Opposition factor: 40% increase in effective wave chop\n"
        else:
            if niwa_tide:
                report += f"\n🌊 **Tide State: Auto-detected from NIWA data**\n"
                # Tide state will be shown in opposition_summary if NIWA data is available
            else:
                report += f"\n🌊 **Tide State: Not specified** (mention 'flood', 'ebb', 'rising', or 'falling' for analysis)\n"
        
        # Add NIWA tide magnitude info
        if niwa_tide:
            report += f"\n🌊 **NIWA Tide Data:**\n"
            report += f"   {niwa_tide['description']}\n"
            report += f"   Magnitude multiplier: {niwa_tide['magnitude_factor']:.1f}x\n"
            if niwa_tide['magnitude'] == "SPRING":
                report += f"   ⚠️ **Spring tide: More chop and current**\n"
            elif niwa_tide['magnitude'] == "NEAP":
                report += f"   ✅ **Neap tide: Calmer conditions**\n"
        
        report += f"\n💡 **Wind directions shown (0°=N, 90°=E, 180°=S, 270°=W)**\n"
        
        # Add weather pattern analysis from boating guides
        if wind and wind_dir:
            avg_wind = sum(wind[:3]) / len(wind[:3]) if wind else 0
            avg_wind_dir = sum(wind_dir[:3]) / len(wind_dir[:3]) if wind_dir else 0
            
            pattern_analysis = analyze_weather_patterns(
                wind_speed_kt=avg_wind,
                wind_direction=avg_wind_dir,
                tide_state=tide_state,
                location=location_name,
                boat_size=boat_size
            )
            if pattern_analysis:
                report += f"\n{pattern_analysis}"
        
        # Add location recommendations based on weather conditions
        location_recs = recommend_fishing_locations(
            wind, wave, boat_class, boat_size, 
            tide_state=tide_state,
            tide_info=niwa_tide,
            num_recommendations=3
        )
        if location_recs:
            report += location_recs
        
        return report
        
    except requests.exceptions.Timeout:
        return "⚠️ API timeout. Use WebConsensus."
    except Exception as e:
        return f"⚠️ Error: {type(e).__name__}: {str(e)}\n\nUse WebConsensus tool."

def marine_web_search(query):
    """Web search - simplified."""
    return ("💡 Manual weather check recommended:\n\n"
           "🌐 **Windy.com**: https://www.windy.com\n"
           "🌐 **PredictWind**: https://www.predictwind.com/forecast/map\n"
           "🌐 **MetService Marine**: https://www.metservice.com/marine/regions/cook-strait\n"
           "🌐 **Yr.no**: https://www.yr.no/en")

def parse_weekend_dates(which_weekend="this"):
    """Calculate weekend dates including Friday.
    
    Args:
        which_weekend: "this" for coming Friday-Sunday, "next" for the Friday-Sunday after that
        
    Returns:
        (friday, saturday, sunday, days_ahead)
        - For "this weekend": First Friday from today (including today), plus Sat/Sun
        - For "next weekend": Skip the first Friday, get the next Friday after that, plus Sat/Sun
    """
    today = datetime.now()
    
    if which_weekend == "this":
        # Find first Friday from today (including today)
        # Friday = 4 (Monday=0, Sunday=6)
        days_until_friday = (4 - today.weekday()) % 7
        friday = today + timedelta(days=days_until_friday)
    else:  # "next" weekend
        # Find first Friday, then skip it (add 7 days) to get the next Friday
        days_until_first_friday = (4 - today.weekday()) % 7
        friday = today + timedelta(days=days_until_first_friday + 7)
    
    saturday = friday + timedelta(days=1)
    sunday = friday + timedelta(days=2)
    
    # Calculate days ahead (for forecast length)
    days_ahead = (sunday - today).days + 1
    
    return friday, saturday, sunday, days_ahead

def fetch_weather_wrapper(input_str):
    """Wrapper that handles location and optional days parameter.
    
    Accepts:
    - "location" (defaults to 2 days)
    - "location, days" (e.g., "mana marina, 7" for 7-day forecast)
    - Natural language: "location for next week", "location next 3 days", etc.
    - "location this weekend" / "location next weekend" (calculates actual Fri+Sat+Sun dates)
    
    Validates requests and caps at 10 days (marine forecast reliability limit).
    """
    input_lower = str(input_str).lower()
    location = input_str
    days = 2  # default
    requested_days = None
    weekend_context = None
    
    # Handle "this weekend" specially to get proper Friday + Saturday + Sunday dates
    if 'this weekend' in input_lower:
        friday, saturday, sunday, days_needed = parse_weekend_dates('this')
        requested_days = days_needed
        days = days_needed
        weekend_context = f"(Friday {friday.strftime('%d %b')} – Sunday {sunday.strftime('%d %b')})"
        # Remove weekend phrases from location string
        location = input_lower.replace('this weekend', '', 1).replace('weekend', '', 1).strip(' ,for\t')
    # Handle "next weekend" separately to get the following Friday-Sunday
    elif 'next weekend' in input_lower:
        friday, saturday, sunday, days_needed = parse_weekend_dates('next')
        requested_days = days_needed
        days = days_needed
        weekend_context = f"(Friday {friday.strftime('%d %b')} – Sunday {sunday.strftime('%d %b')})"
        # Remove weekend phrases from location string
        location = input_lower.replace('next weekend', '', 1).replace('weekend', '', 1).strip(' ,for\t')
    elif 'weekend' in input_lower:
        # Handle just "weekend" as this coming weekend
        friday, saturday, sunday, days_needed = parse_weekend_dates('this')
        requested_days = days_needed
        days = days_needed
        weekend_context = f"(Friday {friday.strftime('%d %b')} – Sunday {sunday.strftime('%d %b')})"
        location = input_lower.replace('weekend', '', 1).strip(' ,for\t')
    
    # Try other time phrases if not weekend
    if requested_days is None:
        time_phrases = {
            'next week': 7, 'this week': 7, 'week': 7, '7 days': 7,
            'next 3 days': 3, 'next three days': 3, '3 days': 3, 'three days': 3,
            'next 5 days': 5, 'next five days': 5, '5 days': 5, 'five days': 5,
            'next 10 days': 10, 'next ten days': 10, '10 days': 10, 'ten days': 10,
            'fortnight': 14, 'next fortnight': 14,
            'today': 1, 'tomorrow': 1,
        }
        
        for phrase, day_count in time_phrases.items():
            if phrase in input_lower:
                requested_days = day_count
                days = day_count
                # Remove the time phrase from location string
                location = input_str.replace(phrase, '', 1).replace(phrase.title(), '', 1).strip(' ,for\t')
                break
    
    # If no natural language match, try comma-separated format
    if requested_days is None and ',' in str(input_str):
        parts = [p.strip() for p in str(input_str).split(',')]
        location = parts[0]
        if len(parts) > 1:
            try:
                requested_days = int(parts[1])
                days = requested_days
            except ValueError:
                pass  # keep default
    
    # If user requested more than 10 days, inform them of the limit
    if requested_days and requested_days > 10:
        result = fetch_marine_data(location, 10)  # Get 10-day forecast
        return (f"⚠️ **Note:** You requested a {requested_days}-day forecast, but marine weather forecasts "
                f"beyond 10 days are generally unreliable due to rapidly changing conditions. "
                f"Showing 10-day forecast instead.\n\n{result}")
    
    result = fetch_marine_data(location, days)
    # Add weekend context to result if applicable
    if weekend_context:
        result = f"📅 **{weekend_context}**\n\n{result}"
    return result

def search_books(query):
    """Search maritime PDFs for hazards, local knowledge, and safety guidelines.
    
    Comprehensive search across Cook Strait Boating Guides and Cockpit Guide
    for location-specific hazards, tidal information, weather effects, and safety advice.
    """
    try:
        vector_db = Chroma(persist_directory="./chroma_db", embedding_function=OpenAIEmbeddings())
        
        # Build comprehensive search queries for safety assessment
        search_queries = [
            query,  # Original query
            f"{query} hazards rocks rips tides currents",
            f"{query} safety conditions weather patterns wind",
            f"Cook Strait {query} boating guide conditions",
            f"{query} crossing dangers opposition tide"
        ]
        
        all_docs = []
        for search_query in search_queries:
            try:
                # Try with maritime category filter
                docs = vector_db.similarity_search(search_query, k=2, filter={"category": "maritime"})
                if not docs:
                    # Fallback without filter
                    docs = vector_db.similarity_search(search_query, k=2)
                all_docs.extend(docs)
            except:
                # Silently skip if search fails
                pass
        
        if not all_docs:
            return "ℹ️ No detailed guidance available for this location."
        
        # Remove duplicates
        seen = set()
        unique_docs = []
        for doc in all_docs:
            content = doc.page_content
            if content not in seen:
                seen.add(content)
                unique_docs.append(doc)
        
        # Format results
        result = "═══ SAFETY & LOCAL KNOWLEDGE (from Boating Guides) ═══\n\n"
        for i, doc in enumerate(unique_docs[:5], 1):  # Top 5 most relevant
            source = doc.metadata.get('filename', 'Guide').replace('.pdf', '')
            page = doc.metadata.get('page', '?')
            content = doc.page_content[:280].strip()
            # Clean up whitespace
            content = ' '.join(content.split())
            result += f"{i}. [{source}] {content}...\n\n"
        
        return result
    except Exception as e:
        return "ℹ️ Knowledge base temporarily unavailable."

def analyze_weather_patterns(wind_speed_kt, wind_direction, tide_state, location, boat_size):
    """Use boating guide knowledge to analyze how weather patterns affect water conditions.
    
    This function searches the Cook Strait Boating Guides and Cockpit Guide for
    information about how specific wind patterns and tide states create water conditions.
    
    Args:
        wind_speed_kt: Wind speed in knots
        wind_direction: Wind direction in degrees (0-360, 0=N, 90=E, 180=S, 270=W)
        tide_state: Tide state if known (flood, ebb, rising, falling) or None
        location: Location name
        boat_size: Boat size in meters
        
    Returns:
        str with detailed weather pattern analysis from boating guides
    """
    try:
        vector_db = Chroma(persist_directory="./chroma_db", embedding_function=OpenAIEmbeddings())
        
        # Convert wind direction to compass direction
        compass_dirs = ["northerlies", "NNE", "northeasterlies", "ENE", 
                       "easterlies", "ESE", "southeasterlies", "SSE",
                       "southerlies", "SSW", "southwesterlies", "WSW", 
                       "westerlies", "WNW", "northwesterlies", "NNW"]
        compass_idx = int((wind_direction + 11.25) / 22.5) % 16
        wind_dir_name = compass_dirs[compass_idx]
        
        # Build a comprehensive query about this specific weather pattern
        queries = [
            f"{wind_dir_name} wind {wind_speed_kt} knots Cook Strait {location}",
            f"weather patterns wind direction sea state chop {wind_dir_name}",
            f"wind tide opposition steep seas safety {tide_state}",
            f"boating conditions {location} northerlies southerlies exposed areas",
            f"Cook Strait Boating Guide weather seasonal conditions hazards"
        ]
        
        # Gather insights from multiple angle searches
        all_docs = []
        for query in queries:
            try:
                docs = vector_db.similarity_search(query, k=2, filter={"category": "maritime"})
                all_docs.extend(docs)
            except:
                try:
                    docs = vector_db.similarity_search(query, k=2)
                    all_docs.extend(docs)
                except:
                    pass
        
        if not all_docs:
            return ""
        
        # Remove duplicates while preserving order
        seen = set()
        unique_docs = []
        for doc in all_docs:
            content = doc.page_content
            if content not in seen:
                seen.add(content)
                unique_docs.append(doc)
        
        # Format the analysis
        result = "🌊 **WEATHER PATTERN ANALYSIS (from Boating Guides):**\n\n"
        for i, doc in enumerate(unique_docs[:4], 1):  # Top 4 most relevant
            source = doc.metadata.get('filename', 'Guide').replace('.pdf', '')
            content = doc.page_content[:250].strip()
            # Clean up content to remove page breaks and excess whitespace
            content = ' '.join(content.split())
            result += f"• {content}\n\n"
        
        return result
        
    except Exception as e:
        return ""

def search_fishing_reports(query):
    """Search fishing reports for species, techniques, conditions, and local fishing knowledge."""
    try:
        vector_db = Chroma(persist_directory="./chroma_db", embedding_function=OpenAIEmbeddings())
        # Search for fishing reports
        docs = vector_db.similarity_search(query, k=4, filter={"category": "fishing_reports"})
        
        # Fallback without filter if database doesn't have categories yet
        if not docs:
            docs = vector_db.similarity_search(query + " fishing", k=4)
        
        if not docs:
            return "No fishing reports found. Add fishing reports to the fishing_reports folder and run ingest_knowledge.py"
        
        result = "═══ FISHING REPORTS ═══\n\n"
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get('filename', doc.metadata.get('source', 'Unknown'))
            content = doc.page_content[:400].strip()
            result += f"🎣 {source}\n{content}...\n\n"
        
        return result
    except Exception as e:
        return "⚠️ Fishing reports unavailable. Run ingest_knowledge.py to add fishing data."

def search_mooring_locations(query):
    """
    Location-aware search for mooring and anchorage information.
    Supports multi-day trip analysis and proximity filtering.
    
    Args:
        query: Can include location, weather conditions, and trip duration
               Examples: "sheltered from northerly, 3 day trip"
               "Ship Cove area, southerly winds"
    """
    try:
        # Extract trip duration if mentioned
        trip_duration = extract_trip_duration(query)
        if trip_duration:
            duration_note = f" for {trip_duration}-day trip"
        else:
            duration_note = ""
        
        # Parse user location from query
        user_location, location_name = parse_location_zone(query)
        
        vector_db = Chroma(persist_directory="./chroma_db", embedding_function=OpenAIEmbeddings())
        
        # Search for mooring/anchorage locations with expanded query
        search_query = query + " anchorage mooring bay shelter"
        docs = vector_db.similarity_search(search_query, k=15, filter={"category": "mooring_locations"})
        
        if not docs:
            docs = vector_db.similarity_search(query, k=10)
        
        if not docs:
            return f"❓ I need more location information. Which area of the Sounds are you in or heading to? (e.g., 'Tory Channel', 'Outer QCS', 'Ship Cove area', 'Port Underwood')"
        
        # Extract coordinates and build mooring dicts from docs
        moorings_with_coords = []
        for doc in docs:
            mooring_dict = {
                'name': doc.metadata.get('filename', 'Unknown location'),
                'content': doc.page_content,
                'coordinates': extract_location_coordinates(doc.page_content),
                'distance': None
            }
            moorings_with_coords.append(mooring_dict)
        
        # Filter by distance if user location is known
        if user_location:
            nearby_moorings = filter_moorings_by_distance(
                moorings_with_coords, 
                user_location, 
                max_distance_nm=20.0
            )
            
            # If we have nearby moorings, use them; otherwise use all
            if nearby_moorings:
                moorings_display = nearby_moorings[:5]
            else:
                moorings_display = [(m, None) for m in moorings_with_coords[:5]]
        else:
            moorings_display = [(m, None) for m in moorings_with_coords[:5]]
        
        # Build response
        result = f"⚓ **MOORING & ANCHORAGE RECOMMENDATIONS{duration_note}**\n\n"
        
        if user_location:
            result += f"📍 Based on your location in/near **{location_name}**:\n\n"
        
        # Extract weather info from query for suitability analysis
        wind_direction = ""
        if "north" in query.lower():
            wind_direction = "northerly"
        elif "south" in query.lower():
            wind_direction = "southerly"
        elif "east" in query.lower():
            wind_direction = "easterly"
        elif "west" in query.lower():
            wind_direction = "westerly"
        
        for i, (mooring, distance) in enumerate(moorings_display, 1):
            result += f"\n**{i}. {mooring['name']}**"
            
            if distance:
                result += f" ({distance:.1f}nm away)"
            
            # Extract key info from content
            content = mooring['content']
            lines = content.split('\n')
            
            # Get first few lines of description
            desc_lines = [l.strip() for l in lines[1:4] if l.strip() and not re.match(r'^[A-Z][a-z]+:\s*', l)]
            if desc_lines:
                result += f"\n{desc_lines[0][:150]}..."
            
            # Look for shelter info
            if wind_direction and wind_direction.lower() in content.lower():
                result += f"\n✅ **Shelter:** Good protection from {wind_direction}s"
            elif "shelter" in content.lower():
                result += f"\n✅ **Shelter:** Check detailed notes for specific wind directions"
            
            # Trip duration note
            if trip_duration:
                result += f"\n⏱️ Suitable for {trip_duration}-day stay"
            
            result += "\n"
        
        result += f"\n💡 **Tip:** Ask for more details about any location (depth, hazards, facilities)"
        return result
        
    except Exception as e:
        return f"⚠️ Error searching mooring data: {str(e)}. Please ask for a specific location name (e.g., 'Ship Cove', 'Port Underwood') or which area of the Sounds you're in."

def fetch_bite_times_wrapper(days_input):
    """Fetch bite times from fishing.net.nz for fishing recommendations"""
    try:
        # Parse input - might be just days or "location, days"
        days = 3  # default
        
        if 'day' in days_input.lower():
            # Try to extract number
            import re
            match = re.search(r'(\d+)', days_input)
            if match:
                days = min(int(match.group(1)), 14)  # Max 14 days
        
        return get_bite_times_for_agent(location="wellington", days=days)
    except Exception as e:
        return f"⚠️ Bite times currently unavailable. Visit https://www.fishing.net.nz/fishing-advice/bite-times/ for live data. Error: {str(e)}"

def get_updated_executor():
    """Create agent with smart journey planning for both crossings and local trips."""
    now = datetime.now()
    current_time_str = now.strftime("%A, %B %d, %Y, %H:%M NZDT")
    
    template = """You are Cook Strait Navigator - expert marine safety advisor for New Zealand waters.

Current Time: {current_time_str}
🧠 CONTEXT AWARENESS:
- If the query is just an entrance name ("Tory", "Koamaru", etc.), this is a follow-up answer to your previous entrance clarification question
- Treat it as: "I want a Cook Strait crossing forecast to [entrance name]"
- Proceed immediately with weather checks for that entrance
� RESPONSE FORMAT (CRITICAL):
You MUST follow this exact format:
- Thought: [describe what you're thinking or what you'll do next]
- Action: [tool name]
- Action Input: [input for the tool]
- Observation: [result from tool - this comes automatically]
- Thought: [analyze the observation]
- Action: [next tool] OR Final Answer: [if done]

When providing your final answer:
1. Write your last Thought on one line
2. Press enter to create a NEW LINE
3. Write "Final Answer:" on that new line
4. Write your formatted response

CORRECT FORMAT:
Thought: I have all the data needed to answer.

Final Answer:

[Your response here]

WRONG FORMAT (causes errors):
Thought:Final Answer: [response]  ← NO! Missing line break!

�🚨 CRITICAL SAFETY RULES:
1. Wind > 20kt OR Wave > 1.5m = NO-GO for recreational vessels
2. ALWAYS consider return conditions - even day trips need safe return timing before weather deteriorates
3. Watch for wind changes, spring tides against wind, and deteriorating trends
4. For day trips: Provide specific "return by" times when conditions will worsen
5. For multi-day forecasts, identify BEST and WORST days
6. DEFAULT DEPARTURE: If no departure location specified for crossings, assume "mana marina" (-41.10108°S, 174.86700°E)

📋 THREE TYPES OF QUERIES:

**TYPE 1: LOCAL TRIPS** (fishing, day trips from one location)
Workflow:
1. Check weather at the location
2. Check LocalKnowledge for hazards (especially tide information)
3. Analyze 48hr forecast for:
   - Best weather windows (low wind, calm seas)
   - Weather changes (wind shifts, building seas)
   - **RETURN timing**: When conditions deteriorate during the day
   - Tide considerations (if mentioned in hazards) - watch for tide running against wind
   - Safe return windows before wind builds or conditions worsen
4. Recommend BEST days/times with SPECIFIC RETURN ADVICE
5. Warn if conditions change rapidly (e.g., "depart 8am, return by 2pm before northerlies build")

**CRITICAL for day trips**: Always analyze the FULL day pattern and provide safe return timing, not just departure conditions!

**TYPE 2: COOK STRAIT CROSSINGS** (to Marlborough Sounds, across strait)
‼️ SPECIAL RULES:
   → If query is ONLY an entrance name ("Tory", "Koamaru", etc.) with NO other context:
      • Treat this as answering a previous entrance clarification question
      • Proceed immediately with full crossing forecast to that entrance
      • Use "mana marina" as departure
   
   → If query mentions "Marlborough Sounds" or "the Sounds" WITHOUT specifying entrance:
      • IMMEDIATELY ask "Which entrance: Tory Channel (Eastern) or Cape Koamaru (Northern)?" 
      • DO NOT check weather APIs until entrance is specified!
      • RECOGNIZE short answers: "Tory", "Tory Channel", "Koamaru", "Cape Koamaru", "Eastern", "Northern" are all valid

Workflow (once entrance is known):
1. If no departure specified in query, use "mana marina" as default
2. Check departure location weather
3. Check Cook Strait central weather
4. Check specific entrance weather (tory channel OR cape koamaru)
5. Check destination hazards
6. Analyze outbound AND return conditions
7. Calculate safe return window before deterioration

**TYPE 3: BEST TIME ANALYSIS** (finding optimal windows over multiple days)
Examples: "When's the best time to go to the Sounds in the next week?" or "Which day is best for fishing at Pukerua Bay in the next 5 days?"

Workflow:
1. Determine timeframe from query (week = 7 days, 3 days, 5 days, 10 days, etc. - MAX 10 days)
2. For Cook Strait crossings: Check if entrance needs clarification FIRST (see TYPE 2 rule above)
3. Fetch extended forecast using days parameter in WeatherTideAPI (e.g., "location, 7" for 7 days)
4. Analyze ALL periods to find BEST weather windows
5. Identify TOP 3 recommended times with specific departure windows
6. Flag any NO-GO periods
7. Provide clear recommendation with best day/time choices

Note: Marine forecasts beyond 10 days are unreliable - if user asks for more, use 10 days and mention the limitation.

**TYPE 4: FISHING RECOMMENDATIONS** (location suggestions based on weather + fishing reports)
Examples: "Where should I go fishing on Wednesday?" or "Best fishing spot for this weekend based on conditions?"

Workflow:
1. Fetch weather forecast for the requested timeframe using WeatherTideAPI with extended days parameter
2. Identify the best weather day(s) considering:
   - Wind speed and direction
   - Wave height
   - Tide timing (from forecast output)
3. Use FishingReports tool to search for locations that match the predicted conditions:
   - Query with weather pattern (e.g., "light northerlies ebbing tide", "calm southerly slack water")
   - Query with target species if mentioned by user
4. Combine weather analysis + fishing report recommendations:
   - State the best day with specific weather conditions
   - Suggest location(s) based on fishing report patterns
   - Include tide timing from forecast
   - **PROVIDE SAFE RETURN TIME** before conditions deteriorate
   - Mention target species and techniques from fishing reports

Example response structure:
"Next Wednesday is looking good, with light 8-12kt northerlies and 0.5m waves. There's an ebbing tide starting around 11am. Based on previous fishing reports, Pukerua Bay is productive in these conditions for snapper and kahawai. Soft baits and stray-lining work well there. Be sure to return by 3pm when the wind is forecast to shift southwest and build to 18kt."

**TYPE 5: MOORING/ANCHORAGE RECOMMENDATIONS** (suggesting safe overnight/shelter locations based on weather)
Examples: "Where should we anchor in the Sounds tonight with northerlies?" or "Best bay to shelter in for tomorrow's southerly?"

Workflow:
1. Fetch weather forecast for the requested timeframe using WeatherTideAPI
2. Identify key weather factors:
   - Wind direction and strength (shelter needed from which direction?)
   - Wind changes (if overnight, what direction changes occur?)
   - Wave conditions (if traveling to the bay)
3. Use MooringLocations tool to search for bays matching the weather conditions:
   - Query with wind direction (e.g., "sheltered from northerly", "protected southwest")
   - Query with specific bay names if mentioned
   - Query with area (e.g., "Queen Charlotte Sound", "Pelorus Sound")
4. Combine weather analysis + mooring location data:
   - State the forecast conditions clearly
   - Recommend bay(s) with appropriate shelter characteristics
   - Note holding ground quality if available
   - Include any hazards or approach considerations
   - If traveling to the bay, specify safe passage times before conditions worsen

Example response structure:
"With 15-20kt northerlies forecast for tonight easing to 8kt by morning, you'll want shelter from the north. Ship Cove in Queen Charlotte Sound offers excellent protection from northerlies with good holding in mud. The entrance is clear but watch for the shallow patch on the western side. Conditions are safe for the passage now (10kt NW) but will build to 18kt by 2pm, so depart before noon."

🎯 ANALYSIS CHECKLIST:
- Identify ✅ SAFE periods (wind <15kt, wave <1m)
- Identify 🟡 CAUTION periods (wind 15-20kt, wave 1-1.5m)
- Identify 🟠 NO-GO periods (wind >20kt, wave >1.5m)
- Note weather TRENDS (improving vs deteriorating)
- Flag wind DIRECTION changes (may affect exposed areas)
- Warn about RAPID changes (e.g., "conditions worsen after 10am")
- **FOR DAY TRIPS**: Analyze FULL DAY pattern and specify safe return times
- **TIDE WARNING**: Note if tide running against wind could create steep seas
- Calculate "return by" times before conditions deteriorate

⚠️ CRITICAL RULES:
- NEVER use placeholder text like "[location]" or "[departure location]" in Action Input. ALWAYS use actual location names from the query or defaults.
- IF query mentions "Marlborough Sounds" or "the Sounds" WITHOUT specifying an entrance, immediately ask which entrance BEFORE making any API calls
- RECOGNIZE entrance answers: Accept "Tory Channel", "Tory", "Cape Koamaru", "Koamaru", "Eastern", "Northern" as valid entrance specifications
- When user responds with ONLY an entrance name (e.g., "Tory" or "Koamaru" with no other context), this means:
  * They are answering your entrance clarification question
  * You should proceed with a full Cook Strait crossing forecast to that entrance
  * Use default departure "mana marina"
  * Check all three locations: departure, cook strait, and the specified entrance
- For "best time" queries, extract the timeframe from the query and use extended forecast format:
  * "next 3 days" → "location, 3"
  * "this week" or "next week" → "location, 7"
  * "next 10 days" → "location, 10"
  * Maximum is 10 days (marine forecasts beyond this are unreliable)
- For fishing queries requesting location recommendations, use FishingReports tool to match weather patterns with historical fishing success:
  * First check weather forecast for the target day(s)
  * Then query FishingReports with the weather conditions (e.g., "light northerlies ebbing tide")
  * Combine weather + fishing reports to suggest specific locations with species/techniques
  * Always include safe return timing before conditions deteriorate
- **For mooring/anchorage queries:**
  * ALWAYS ask for user's current location in the Sounds if not specified (needed for proximity filtering)
  * ALWAYS call LocalKnowledge tool FIRST to understand wind/sea conditions specific to the area and how different wind directions affect bays
  * Detect multi-day trips using extract_trip_duration patterns ("3 day trip", "3 days", "weekend", "overnight", "4 nights", etc.)
  * For multi-day trips: Fetch extended forecast (3-7 days) and provide DAY-BY-DAY recommendations
  * Analyze how weather CHANGES over the trip duration and recommend mooring movements if needed
  * For each bay recommended, explain: What wind direction provides shelter, how that wind creates sea state, any specific hazards from boating guides
  * Example: "Saturday northerlies → Ship Cove (back bay protected, northerlies funnel through outer Sound creating steep seas outside). Sunday steady. Monday southerlies arrive → move to Port Underwood (opens to north, protected from south)"
  * Always flag if user needs to RELOCATE to a different bay as weather pattern changes
- When you finish gathering all data, write a final "Thought:" describing what you learned, then ON THE NEXT LINE write "Final Answer:" followed by your complete formatted response
- The words "Final Answer:" MUST be on their own line, NEVER on the same line as "Thought:"
- Format: "Thought: [your final thought]\nFinal Answer:\n\n[your response]"

📚 **USING BOATING GUIDES FOR SAFETY ASSESSMENT:**
For ANY weather check (local trips, crossings, best time analysis):
1. **ALWAYS** use LocalKnowledge tool to search for boating guide insights about the location
2. The weather forecast includes **WEATHER PATTERN ANALYSIS** (from Cook Strait Boating Guide 1 & 2 and Cockpit Guide) showing how that specific wind direction and speed affects water conditions
3. Use this pattern analysis alongside raw forecast data - it's not just wind speed and wave height, but HOW different wind patterns create dangerous conditions
   - E.g., northerlies may create different chop patterns than southerlies in the same location
   - Tide running against wind creates steeper, more dangerous seas
   - Spring tides amplify effects, neap tides reduce them
4. When analyzing Cook Strait crossings, reference the hazard information for opposition conditions, tidal races, and entrance-specific dangers
5. Combine weather patterns + boating guide knowledge + actual forecast to provide nuanced safety advice
   - Don't just say "wind is 15kt" - explain what that means in context of the location's specific geography and weather patterns

Available tools:
{tools}

Tool names: {tool_names}

RESPONSE FORMATS:

**For ENTRANCE-ONLY QUERY (follow-up answer):**
Example: User previously asked about "the Sounds" and you asked which entrance. Now they reply:
Question: Koamaru
Thought: This is just an entrance name with no other context. The user is answering my previous question about which entrance to use. I should proceed with a Cook Strait crossing forecast to Cape Koamaru from the default departure (mana marina).
Action: WeatherTideAPI
Action Input: mana marina
[... continue with full crossing workflow: departure → cook strait → koamaru → hazards → final answer ...]

---

**For LOCAL TRIPS:**
Example: "What's the weather like for fishing at Plimmerton this weekend?"
Question: {input}
Thought: This is a local trip from Plimmerton. I need to check weather and hazards there, then analyze FULL DAY patterns including return timing.
Action: WeatherTideAPI
Action Input: plimmerton
Observation: [48hr forecast]
Thought: Looking at the forecast, I can see [day 1 pattern: calm morning but wind builds afternoon], [day 2 pattern]. I need to identify safe departure AND return windows. Let me check for local hazards and tide information.
Action: LocalKnowledge
Action Input: plimmerton
Observation: [hazards]
Thought: Now I have all the data. For Saturday: excellent conditions 8am-12pm, but wind builds to 18kt by 3pm so must return by 1pm. For Sunday: moderate all day. I can provide specific departure and return advice for each option.

Final Answer:

**🎣 FISHING FORECAST: [Location]**

**BEST DAYS/TIMES:**
✅ **[Day & Date], Depart [Time]**
   - Wind: [X]kt | Wave: [X]m - Excellent conditions
   - ⚓ **Return by [Time]**: Conditions remain good until [time/reason]
   
✅ **[Day & Date], Depart [Time]**
   - Wind: [X]kt | Wave: [X]m - Good conditions
   - ⚠️ **Return by [Time]**: Wind builds to [X]kt after this

**AVOID:**
🟠 **[Day & Time]**: Wind [X]kt, Wave [X]m - [Reason]

**WEATHER PATTERN:**
- [Describe overall trend, e.g., "Calm Friday morning, building northerlies Friday afternoon"]
- [Note any changes, e.g., "Wind shifts to southerly Saturday bringing chop"]
- [Any tide vs wind warnings, e.g., "Spring tide running against southerlies creates steep seas"]

**LOCAL HAZARDS:**
- [List relevant hazards from knowledge base, especially tide-related]

**RECOMMENDATION:** 
[Summary with best option including specific return timing. Example: "Best option is Friday 8am-1pm. Depart early, return by 1pm before northerlies build to 18kt in afternoon."]

---

**For FISHING RECOMMENDATIONS (location suggestion based on weather + reports):**
Example: "Where should I go fishing on Wednesday?" or "Best fishing spot this weekend based on conditions?"
Question: {input}
Thought: This is a fishing recommendation query. I need to first check the weather forecast for the specified day(s), then search fishing reports to match locations with those conditions.
Action: WeatherTideAPI
Action Input: mana marina, 5
Observation: [multi-day forecast showing Wednesday has light 8-12kt northerlies, 0.5m waves, ebbing tide from 11am]
Thought: Wednesday looks excellent with light northerlies and calm seas. Now I'll search fishing reports to find which locations are productive in these conditions.
Action: FishingReports
Action Input: light northerlies ebbing tide
Observation: [fishing reports showing Pukerua Bay produces well in light northerlies with ebbing tide for snapper and kahawai, soft baits effective]
Thought: Perfect! I have weather conditions and matching fishing location data. I can now provide a complete recommendation with specific timing and safe return window.

Final Answer:

**🎣 FISHING RECOMMENDATION**

**BEST DAY: Wednesday [Date]**

**CONDITIONS:**
- Wind: 8-12kt northerlies  
- Waves: 0.5m - Excellent
- Tide: Ebbing from 11am

**RECOMMENDED LOCATION: Pukerua Bay**
Based on previous fishing reports, Pukerua Bay is highly productive in these conditions:
- **Target Species**: Snapper, kahawai, gurnard
- **Techniques**: Soft baits and stray-lining work well  
- **Best Time**: Fish the ebbing tide from 11am-2pm

**TIMING:**
- ✅ **Depart**: 10am (set up before tide turns)
- ⚓ **Return by**: 3pm - Wind forecast to shift southwest and build to 18kt later afternoon

**ALTERNATIVE:** Thursday also looks reasonable but with slightly stronger winds (12-15kt southerlies).

**SAFETY NOTE:** Monitor wind shifts. If southerlies arrive earlier than forecast, return immediately as this location is exposed to southerly chop.

---

**For CROSSINGS (with Sounds entrance clarification):**
Example: "Can I cross to the Marlborough Sounds this weekend?"
Question: {input}
Thought: The user wants to go to the Marlborough Sounds but hasn't specified which entrance. I need to ask for clarification BEFORE checking any weather data.

Final Answer:

⚠️ **CLARIFICATION NEEDED**

The Marlborough Sounds has TWO main entrances:

1️⃣ **TORY CHANNEL** (Eastern Entrance)
   - More direct route from Wellington
   - Popular for Picton access
   - Just reply with "Tory" or "Tory Channel"

2️⃣ **CAPE KOAMARU** (Northern Entrance)  
   - Access to Queen Charlotte Sound
   - More exposed to northerlies
   - Just reply with "Koamaru" or "Cape Koamaru"

❓ **Which entrance will you be using?**

Once you specify, I can provide a detailed crossing forecast including departure times, weather conditions, and return windows.

---

**For CROSSINGS (after entrance is specified):**
Example: User first asked "Can I go to the Sounds?" and then replied "Koamaru"
Question: Koamaru
Thought: The user has specified Cape Koamaru as their entrance choice. This is a follow-up answer to my entrance clarification question. I should now proceed with checking weather for a Cook Strait crossing to Cape Koamaru. Using default departure "mana marina".
Action: WeatherTideAPI
Action Input: mana marina
Observation: [forecast data]
Thought: Got departure forecast. Now checking Cook Strait central.
Action: WeatherTideAPI
Action Input: cook strait
Observation: [forecast data]
Thought: Got Cook Strait forecast. Now checking Cape Koamaru destination.
Action: WeatherTideAPI
Action Input: koamaru
Observation: [forecast data]
Thought: Got destination forecast. Now checking local hazards.
Action: LocalKnowledge
Action Input: cape koamaru
Observation: [hazards]
Thought: I now have all the data to provide a complete crossing forecast from Mana Marina to Cape Koamaru.

Final Answer:

**⚓ STRAIT CROSSING: Mana Marina → Cape Koamaru**
[... full crossing recommendation with outbound/return analysis ...]

---

**For CROSSINGS (entrance specified in original query):**

**For BEST TIME ANALYSIS (multi-day):**
Example 1: "When's the best time to go fishing at Pukerua Bay over the next week?"
Question: {input}
Thought: This is a best-time analysis query for 7 days at Pukerua Bay. I need to fetch an extended forecast to identify the optimal windows including safe return timing.
Action: WeatherTideAPI
Action Input: pukerua bay, 7
Observation: [7-day forecast with many time periods]
Thought: I have 7 days of data. Analyzing all periods to find the best fishing conditions. For each good window, I need to identify when conditions deteriorate so I can specify safe return times. Let me also check for local hazards and tide information.
Action: LocalKnowledge
Action Input: pukerua bay
Observation: [hazards]
Thought: I've analyzed the full week forecast. Best option is Friday 7am-1pm (return by 1pm before wind builds to 18kt). Second best is Sunday morning with all-day good conditions. Third is Wednesday but watch afternoon sea breeze.

Final Answer:

**🎣 BEST FISHING TIMES: Pukerua Bay (Next 7 Days)**

**TOP RECOMMENDATIONS:**
🥇 **BEST: [Day] [Date], Depart [Time]**
   - Wind: [X]kt | Wave: [X]m
   - Conditions: [Description]
   - ⚓ **Return by [Time]**: [Reason, e.g., "Wind builds to 20kt after 2pm"]

🥈 **GOOD: [Day] [Date], Depart [Time]**  
   - Wind: [X]kt | Wave: [X]m
   - Conditions: [Description]
   - ⚓ **Return by [Time]**: [Reason]

🥉 **FAIR: [Day] [Date], Depart [Time]**
   - Wind: [X]kt | Wave: [X]m  
   - Conditions: [Description]
   - ⚠️ **Return by [Time]**: [Reason]

**AVOID:**
🟠 **[Days/Times]**: [Conditions] - [Reason]

**WEEKLY PATTERN:**
- [Describe overall weather trend across the week]
- [Note any significant changes and when to avoid being on water]

**LOCAL HAZARDS:**
- [Relevant hazards, especially tide-related]

**RECOMMENDATION:** [Pick the absolute best option]

---

Example 2: "What's the best day in the next 5 days to cross to Tory Channel?"
Question: {input}
Thought: This is a best-time analysis for a 5-day Cook Strait crossing to Tory Channel. I need to check 5-day forecasts for departure, Cook Strait, and Tory Channel.
Action: WeatherTideAPI
Action Input: mana marina, 5
Observation: [5-day forecast]
Thought: Got 5 days of departure data. Now checking Cook Strait.
Action: WeatherTideAPI
Action Input: cook strait, 5
Observation: [5-day forecast]
Thought: Got 5 days of Cook Strait data. Now checking Tory Channel.
Action: WeatherTideAPI
Action Input: tory channel, 5
Observation: [5-day forecast]
Thought: Have all 5-day forecasts. Analyzing to find the best crossing window with safe conditions throughout the route.

Final Answer:

**⚓ BEST CROSSING WINDOWS: Mana Marina → Tory Channel (Next 5 Days)**

**TOP RECOMMENDATIONS:**
🥇 **BEST: [Day] [Date], Depart [Time]**
   - All locations show excellent conditions
   - Safe return window: [Hours]
   
🥈 **GOOD: [Day] [Date], Depart [Time]**
   - Good conditions, minor caution on return
   
🥉 **FAIR: [Day] [Date], Depart [Time]**
   - Acceptable but watch [specific concern]

**5-DAY PATTERN:**
- [Describe trend]

**RECOMMENDATION:** [Best specific option]

**LOCAL HAZARDS:**
- [Relevant hazards]

**RECOMMENDATION:** [Pick the absolute best option]

---

**For CROSSINGS (with known entrance):**
Example: "Can I cross to Tory Channel tomorrow?"
Question: {input}  
Thought: This is a Cook Strait crossing to Tory Channel. The entrance is specified, so I can proceed. User hasn't specified departure, so I'll use default "mana marina". I need to check departure, Cook Strait, destination weather, then hazards.
Action: WeatherTideAPI
Action Input: mana marina
Observation: [forecast]
Thought: Got departure forecast. Now checking Cook Strait central.
Action: WeatherTideAPI  
Action Input: cook strait
Observation: [forecast]
Thought: Got Cook Strait forecast. Now checking Tory Channel destination.
Action: WeatherTideAPI
Action Input: tory channel
Observation: [forecast]
Thought: Got destination forecast. Now checking local hazards.
Action: LocalKnowledge
Action Input: tory channel
Observation: [hazards]
Thought: Perfect. I now have all the data: departure conditions, Cook Strait conditions, destination conditions, and local hazards. I can analyze everything and provide a complete crossing recommendation.

Final Answer:

**⚓ STRAIT CROSSING: [Departure] → [Destination]**

**RECOMMENDATION: [GO/NO-GO]**

**OUTBOUND:** 
- Depart: [Time window]
- [Departure]: [conditions]
- Cook Strait: [conditions]
- [Destination]: [conditions]

**RETURN:**
⚠️ **CRITICAL:** Return by [time] - conditions deteriorate to [X]kt/[X]m after this
- [Describe deterioration pattern]

**HAZARDS:**
- [List from knowledge base]

**FINAL ADVICE:** [Clear recommendation with timing]

---

**For MOORING/ANCHORAGE RECOMMENDATIONS (with location awareness and multi-day analysis):**
Example 1: "Best anchorages for a 3-day trip to the Sounds starting Saturday?"
Question: {input}
Thought: This is a multi-day trip mooring query. I need to:
1. Detect it's a 3-day trip
2. Ask where in the Sounds they'll be based/starting from
3. Fetch 3-7 day forecast showing wind patterns and sea state
4. Search for mooring locations suitable for their location and weather conditions
5. Check LocalKnowledge for bay-specific wind/sea conditions (how northerlies/southerlies affect each bay)
6. Provide day-by-day recommendations accounting for weather changes

Let me start with the forecast.
Action: WeatherTideAPI
Action Input: queen charlotte sound, 5
Observation: [5-day forecast with wind directions and patterns]
Thought: Got 5-day forecast. Saturday northerlies, Sunday steady, Monday southerly shift. Now let me get bay-specific information about how these wind directions affect anchorages.
Action: LocalKnowledge
Action Input: queen charlotte sound northerly southerly shelter wind conditions
Observation: [wind pattern analysis from boating guides showing how N and S winds affect QCS bays]
Thought: Excellent - now I understand how each wind direction affects the Sound. Now let me search for mooring locations suitable for the forecast pattern.
Action: MooringLocations
Action Input: northerly southerly shelter 3 day trip queen charlotte sound
Observation: [list of bays with their shelter characteristics for different wind directions]
Thought: Perfect. I now have: 1) Forecast with wind patterns, 2) Boating guide details on how those winds affect the area, 3) Mooring locations with shelter ratings. I can provide informed day-by-day recommendations.

Final Answer:

**⚓ 3-DAY MOORING STRATEGY: Marlborough Sounds**

**📍 YOUR LOCATION:** Queen Charlotte Sound

**DAY 1 (Saturday): 12-15kt NORTHERLIES**
🎯 **Recommended:** Ship Cove
- **Forecast:** Northerlies 12-15kt (strong gusty flow through outer Sound - from boating guides)
- **Shelter:** Excellent protection from N winds (back of bay, surrounded by hills)
- **Sea State:** Northerlies create steep seas outside bay but Ship Cove is deeply recessed and protected
- **Approach:** Safe to enter in current conditions - enter with caution, avoiding north headland
- **Setup notes:** Deep water close to shore, good mud holding, DOC facilities

**DAY 2 (Sunday): 10-12kt NORTHERLIES EASING**
🎯 **Recommended:** Ship Cove (stay put - excellent conditions)
- **Forecast:** Northerlies ease to 10-12kt
- **Shelter:** Continues excellent protection - no need to move
- **Sea State:** Swell from previous day eases as wind drops
- **Best for:** Exploring, shore activities, maintenance

**DAY 3 (Monday): 15kt SOUTHERLIES DEVELOPING**
⚠️ **MUST MOVE** - Wind shift makes Ship Cove exposed
- **Forecast:** Wind shifts to southerly 15kt (ebb to southeasterly pattern per boating guides)
- **Current Situation:** Ship Cove's open south aspect becomes exposed - southerlies create surge and swell
- **Recommended Move:** Port Underwood or Te Awaiti Bay (both provide excellent southerly shelter)
- **Movement Timing:** Sunday 5pm (before darkness, while northerlies still provide protection during transit)
- **Transit:** 1.5 hours in light conditions

**OVERALL STRATEGY:**
- Saturday: Northern exposure suitable for northerlies → Ship Cove ✅
- Sunday: Hold position, conditions steady → Ship Cove ✅
- Sunday PM: Anticipate wind shift → Relocate to southerly-protected bay
- Monday: Depart from new protected anchorage in southerly wind

**CRITICAL WIND PATTERN NOTE** (from local boating knowledge):
Northerlies funnel strongly through outer Sound from N sector. Southerlies are less violent but create surge and swell on southern-exposed shorelines. Spring tide amplifies both patterns.

---

Example 2: "Where should we anchor tonight with 18kt southerlies?"
Question: {input}
Thought: This is an immediate (same-night) mooring recommendation. I need location awareness and wind-specific shelter info. Let me first understand how 18kt southerlies affect the Sounds bays.
Action: LocalKnowledge
Action Input: southerly wind 18 knots shelter anchorage Sounds hazards
Observation: [Boating guide info on how southerlies create conditions, which bays have southern exposure, surge patterns, etc.]
Thought: Good - now I understand the hazard pattern. Let me search for moorings with southerly protection.
Action: MooringLocations
Action Input: shelter from southerly 18 knots anchorage
Observation: [mooring recommendations with southerly shelter characteristics]
Thought: Now I have wind pattern info and suitable moorings. I need their location to filter by proximity.

Final Answer:

❓ **QUICK CLARIFICATION:** Where are you currently located in the Sounds? (E.g., "Near Tory Channel entrance", "Outer QCS", "Near Ship Cove")

With **18kt SOUTHERLIES** (creates surge on south-facing shores per boating guides), here are protected options:

✅ **BEST: Port Underwood** (if you can reach it safely - 4-5nm from outer entrance)
- Excellent shelter from S/SE wind - bay opens to N/NW
- Good holding in mud/sand
- Clear approach, watch for fisheries activity
- **Wind Effect:** Southerlies diminish significantly once inside port

✅ **GOOD: Te Awaiti Bay** (closer to Picton, 3nm from typical outer positions)
- Protected from southerlies, opens to north
- Good holding with pick anchor required (mud with seaweed)
- **Wind Effect:** Sheltered in southerlies but exposed to ferry wash
- Shallower than Port Underwood

✅ **ALTERNATIVE: Whekenui Bay**
- Protected from southerlies in lee of western shore
- Less developed but less crowded
- **Wind Effect:** Good protection from S winds, gets some wind funneling from Cook Strait

**CRITICAL CHECK:** Tell me your current position. I can verify safe routing given the wind, check if bays remain accessible in 18kt southerlies, and give you ETA and entry procedures for each option.

Question: {input}
{agent_scratchpad}"""

    prompt = PromptTemplate.from_template(template).partial(current_time_str=current_time_str)
    
    tools = [
        Tool(
            name="WeatherTideAPI", 
            func=fetch_weather_wrapper, 
            description="Get marine weather forecast with wind/wave data and safety flags (✅SAFE/🟡CAUTION/🟠NO-GO). Input format: 'location' for 2-day forecast OR 'location, days' for custom forecasts (e.g., 'mana marina, 7' for 7 days, 'pukerua bay, 5' for 5 days). Maximum 10 days (marine forecasts beyond this are unreliable). Use extended forecasts for 'best time' analysis queries. Locations: mana marina, cook strait, tory channel, cape koamaru, plimmerton, pukerua bay, etc."
        ),
        Tool(
            name="WebConsensus", 
            func=marine_web_search, 
            description="Get links to Windy, PredictWind, MetService. Use for supplemental cross-checking."
        ),
        Tool(
            name="LocalKnowledge", 
            func=search_books, 
            description="Search maritime PDFs for rocks, rips, tide considerations, and local hazards. Essential for understanding area-specific dangers. Input: location name"
        ),
        Tool(
            name="FishingReports", 
            func=search_fishing_reports, 
            description="Search historical fishing reports for species, techniques, best conditions (wind/tide/time), and successful locations. Use when users ask about fishing or want location recommendations based on weather patterns. Input: query about species, location, or conditions (e.g., 'snapper light northerlies', 'Pukerua Bay', 'blue cod ebbing tide')"
        ),
        Tool(
            name="BiteTimesAPI",
            func=fetch_bite_times_wrapper,
            description="Fetch real-time bite times from fishing.net.nz for major and minor feeding windows. Includes sun/moon rise-set times. Use for fishing recommendations to tell users when fish are most active. Input: 'X days' to fetch bite times (e.g., 'next 3 days', 'next 7 days'). References Māori fishing calendar and scientific bite time data."
        ),
        Tool(
            name="MooringLocations",
            func=search_mooring_locations,
            description="Search anchorage and mooring information for Marlborough Sounds bays and harbors. Use when users ask about where to anchor/moor or need recommendations for safe overnight stops based on weather conditions. Input: location name OR weather conditions (e.g., 'Queen Charlotte Sound', 'sheltered from northerly', 'Port Underwood'). Returns bay descriptions, shelter characteristics, holding ground, and hazards."
        )
    ]
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    agent = create_react_agent(llm, tools, prompt)
    
    return AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True, 
        handle_parsing_errors=True,
        max_iterations=15,
        max_execution_time=90
    )

agent = get_updated_executor()