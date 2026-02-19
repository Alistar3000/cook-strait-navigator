#!/usr/bin/env python3
"""Test the weather wrapper and location lookups."""

import os
os.environ['METOCEAN_API_KEY'] = 'test_key'
os.environ['NIWA_API_KEY'] = 'test_key'

# Test days parsing
test_cases = [
    ("mana marina", 2),  # default
    ("plimmerton for next week", 7),
    ("cape koamaru this week", 7),
    ("cook strait, 5 days", 5),
    ("pukerua bay, 10", 10),
    ("tory channel next 3 days", 3),
    ("sinclair head fortnight", 14),
]

# Mock minimal fetch_weather_wrapper to test days parsing
def test_days_parsing():
    print("Testing days parsing in fetch_weather_wrapper:")
    print("=" * 60)
    
    time_phrases = {
        'next week': 7, 'this week': 7, 'week': 7, '7 days': 7,
        'next 3 days': 3, 'next three days': 3, '3 days': 3, 'three days': 3,
        'next 5 days': 5, 'next five days': 5, '5 days': 5, 'five days': 5,
        'next 10 days': 10, 'next ten days': 10, '10 days': 10, 'ten days': 10,
        'fortnight': 14, 'next fortnight': 14,
        'today': 1, 'tomorrow': 1,
        'weekend': 2, 'next weekend': 2,
    }
    
    for input_str, expected_days in test_cases:
        input_lower = input_str.lower()
        location = input_str
        days = 2  # default
        requested_days = None
        
        # Check natural language
        for phrase, day_count in time_phrases.items():
            if phrase in input_lower:
                requested_days = day_count
                days = day_count
                location = input_str.replace(phrase, '').replace(phrase.title(), '').strip(' ,')
                break
        
        # Check comma format
        if requested_days is None and ',' in input_str:
            parts = [p.strip() for p in input_str.split(',')]
            location = parts[0]
            if len(parts) > 1:
                try:
                    requested_days = int(parts[1])
                    days = requested_days
                except ValueError:
                    pass
        
        status = "OK" if days == expected_days else "FAIL"
        print(f"[{status}] '{input_str}' -> {days:2d} days (expected {expected_days:2d}), location: '{location}'")

# Test LOCATIONS lookup
def test_location_lookup():
    print("\n" + "=" * 60)
    print("Testing location lookups:")
    print("=" * 60)
    
    LOCATIONS = {
        "mana marina": {"lat": -41.10108, "lon": 174.86700},
        "mana": {"lat": -41.1141, "lon": 174.8512},
        "plimmerton": {"lat": -41.0821, "lon": 174.8615},
        "pukerua bay": {"lat": -41.0312, "lon": 174.8945},
        "cape koamaru": {"lat": -41.0883, "lon": 174.3814},
    }
    
    locations_to_test = [
        ("plimmerton", True),
        ("Plimmerton", True),
        ("PLIMMERTON", True),
        ("cape koamaru", True),
        ("unknown location", False),
    ]
    
    for loc, should_exist in locations_to_test:
        loc_key = loc.lower().strip()
        exists = loc_key in LOCATIONS
        status = "OK" if exists == should_exist else "FAIL"
        coords = LOCATIONS.get(loc_key, {})
        lat = coords.get("lat", "N/A")
        lon = coords.get("lon", "N/A")
        print(f"[{status}] '{loc}' -> Found: {exists}, Coords: ({lat}, {lon})")

if __name__ == "__main__":
    test_days_parsing()
    test_location_lookup()
    print("\nAll tests complete.")
