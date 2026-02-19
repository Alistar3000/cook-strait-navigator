#!/usr/bin/env python3
"""Test location recommendation system."""

import os
import sys

# Set dummy API keys
os.environ['METOCEAN_API_KEY'] = 'test'
os.environ['NIWA_API_KEY'] = 'test'

# Import the recommendation functions
try:
    from navigator import (
        get_location_recommendation_score,
        recommend_fishing_locations,
        LOCATION_CHARACTERISTICS
    )
    print("✅ Successfully imported recommendation functions\n")
except Exception as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Test case 1: Good conditions for small boat
print("="*60)
print("Test Case 1: Good conditions (calm day)")
print("="*60)

wind_gust = [10, 12, 11, 10, 13, 12]  # 10-13 knots
wave_height = [0.6, 0.7, 0.7, 0.6, 0.8, 0.7]  # 0.6-0.8m
boat_class = "SMALL"
boat_size = 5.0

result = recommend_fishing_locations(wind_gust, wave_height, boat_class, boat_size, tide_state="rising")
print(result)

# Test case 2: Moderate conditions
print("\n" + "="*60)
print("Test Case 2: Moderate wind/waves")
print("="*60)

wind_gust = [18, 20, 19, 21, 22, 20]  # 18-22 knots
wave_height = [1.2, 1.4, 1.3, 1.5, 1.6, 1.4]  # 1.2-1.6m
boat_class = "MEDIUM"
boat_size = 8.0

result = recommend_fishing_locations(wind_gust, wave_height, boat_class, boat_size, tide_state="falling")
print(result)

# Test case 3: Rough conditions
print("\n" + "="*60)
print("Test Case 3: Rough conditions")
print("="*60)

wind_gust = [28, 30, 32, 31, 29, 30]  # 28-32 knots
wave_height = [2.2, 2.4, 2.6, 2.5, 2.3, 2.4]  # 2.2-2.6m
boat_class = "LARGE"
boat_size = 10.0

result = recommend_fishing_locations(wind_gust, wave_height, boat_class, boat_size)
print(result)

# Test individual location scores
print("\n" + "="*60)
print("Test Case 4: Detailed location scoring")
print("="*60)

test_locations = ["mana", "titahi bay", "tory channel", "terawhiti"]
wind = 15  # knots
wave = 1.0  # meters
boat_class = "MEDIUM"

for loc in test_locations:
    score = get_location_recommendation_score(loc, wind, wave, boat_class, "rising")
    print(f"\n{loc.title()}:")
    print(f"  Score: {score['score']:.0f}/100")
    print(f"  Type: {score['type']}, Shelter: {score['shelter']}")
    print(f"  Reason: {score['reason']}")

print("\n✅ All location recommendation tests completed!")
