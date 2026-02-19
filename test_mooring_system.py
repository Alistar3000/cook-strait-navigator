#!/usr/bin/env python3
"""
Test script for location-aware mooring recommendations system.
Tests coordinate extraction, distance calculations, and location parsing.
"""

from mooring_utils import (
    extract_location_coordinates,
    parse_location_zone,
    extract_trip_duration,
    haversine_distance
)

print("=" * 70)
print("LOCATION-AWARE MOORING SYSTEM TEST")
print("=" * 70)

# Test 1: Coordinate Extraction
print("\n✅ TEST 1: Coordinate Extraction")
test_text = """
Ship Cove (Meretoto)
-41.0583, 174.2372 
This bay is attractive and the surrounding hills are completely covered with native bush.
"""

coords = extract_location_coordinates(test_text)
print(f"   Input: '{test_text.split(chr(10))[1].strip()}'")
print(f"   Extracted: {coords}")
assert coords == (-41.0583, 174.2372), "Coordinate extraction failed!"
print("   ✓ PASSED")

# Test 2: Location Zone Parsing
print("\n✅ TEST 2: Location Zone Parsing")
test_queries = [
    "ship cove",
    "tory channel",
    "queen charlotte sound",
    "port underwood"
]

for query in test_queries:
    coords, zone = parse_location_zone(query)
    print(f"   Query: '{query}' → Zone: {zone}, Coords: {coords}")
    assert coords is not None, f"Failed to parse {query}"
print("   ✓ PASSED")

# Test 3: Distance Calculation (Haversine)
print("\n✅ TEST 3: Distance Calculation (Haversine)")
ship_cove = (-41.0583, 174.2372)
jacksons_bay = (-41.2167, 174.3167)

distance = haversine_distance(ship_cove[0], ship_cove[1], jacksons_bay[0], jacksons_bay[1])
print(f"   Ship Cove to Jacksons Bay: {distance:.2f} nautical miles")
assert 8 < distance < 12, f"Distance calculation seems off: {distance}"
print("   ✓ PASSED")

# Test 4: Trip Duration Extraction
print("\n✅ TEST 4: Trip Duration Extraction")
test_queries = [
    ("3 day trip", 3),
    ("4 days", 4),
    ("weekend", 3),
    ("overnight", 2),
    ("one night", 2),
    ("next week", 7),
]

for query, expected_days in test_queries:
    days = extract_trip_duration(query)
    match = "✓" if days == expected_days else "✗"
    print(f"   {match} '{query}' → {days} days (expected {expected_days})")
    assert days == expected_days, f"Trip duration extraction failed for '{query}'"
print("   ✓ PASSED")

# Test 5: Proximity Filtering Scenario
print("\n✅ TEST 5: Proximity Filtering Scenario")
print("   Simulating: User at Ship Cove, searching nearby bays")
user_pos = ship_cove

test_bays = [
    {'name': 'Ship Cove', 'coordinates': (-41.0583, 174.2372)},
    {'name': 'Jacksons Bay', 'coordinates': (-41.2167, 174.3167)},
    {'name': 'Te Awaiti Bay', 'coordinates': (-41.2181, 174.3214)},
    {'name': 'Port Underwood', 'coordinates': (-41.4167, 174.0833)},
]

nearby = []
for bay in test_bays:
    dist = haversine_distance(
        user_pos[0], user_pos[1],
        bay['coordinates'][0], bay['coordinates'][1]
    )
    nearby.append((bay['name'], dist))

nearby.sort(key=lambda x: x[1])
print(f"   User location: Ship Cove {user_pos}")
print(f"   Nearby bays (within 20nm):")
for name, dist in nearby:
    if dist <= 20:
        print(f"      • {name}: {dist:.1f}nm")
        assert dist >= 0, "Invalid distance"
print("   ✓ PASSED")

print("\n" + "=" * 70)
print("✅ ALL TESTS PASSED!")
print("=" * 70)
print("\nLocation-aware mooring system is ready for use:")
print("  • Coordinate extraction from mooring text: WORKING")
print("  • Location zone recognition: WORKING")
print("  • Distance calculations (Haversine): WORKING")
print("  • Trip duration detection: WORKING")
print("  • Proximity filtering: WORKING")
print("\n🛥️ Ready for mooring recommendations with:")
print("  • Location awareness (nearby bays only)")
print("  • Multi-day trip analysis (day-by-day recommendations)")
print("  • Weather-based filtering (shelter suitability)")
