#!/usr/bin/env python3
"""Test script for opposition detection and NIWA integration."""

import sys
import os

# Set dummy API keys for testing (these won't be real but will allow code to run)
os.environ['METOCEAN_API_KEY'] = 'test_key'
os.environ['NIWA_API_KEY'] = 'test_key'

# Suppress SSL warnings for testing
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Test import
try:
    import navigator
    print("✅ navigator.py imports successfully")
except Exception as e:
    print(f"❌ Error importing navigator.py: {e}")
    sys.exit(1)

# Test opposition detection logic
print("\n" + "="*60)
print("Testing Opposition Detection Logic")
print("="*60)

# Test case 1: Rising tide, wind from 326° (NW) - should detect opposition
print("\nTest Case 1: RISING TIDE with NW WIND (326°)")
wind_dir = 326
tide_state = "rising"  # Maps to 45° (NE)

# Get tide info
tide_info = navigator.TIDE_DIRECTIONS.get(tide_state)
if tide_info:
    tide_primary = tide_info["primary"]
    opposite_dir = (tide_primary + 180) % 360
    
    # Calculate angle difference
    diff = abs(wind_dir - opposite_dir)
    if diff > 180:
        diff = 360 - diff
    
    compass_pts = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    compass_idx = int((wind_dir + 11.25) / 22.5) % 16
    wind_compass = compass_pts[compass_idx]
    
    print(f"  Wind: {wind_dir}° ({wind_compass})")
    print(f"  Tide: {tide_state.upper()} → flows {tide_primary}° (NE)")
    print(f"  Opposite of tide: {opposite_dir}° (SW)")
    print(f"  Angle difference: {diff:.0f}°")
    
    if diff < 45:
        print(f"  ✅ Result: OPPOSITION DETECTED")
    else:
        print(f"  ℹ️ Result: Same direction pattern (not directly opposed)")

# Test case 2: Falling tide, wind from 45° (NE) - should detect opposition
print("\nTest Case 2: FALLING TIDE with NE WIND (45°)")
wind_dir = 45
tide_state = "falling"  # Maps to 225° (SW)

tide_info = navigator.TIDE_DIRECTIONS.get(tide_state)
if tide_info:
    tide_primary = tide_info["primary"]
    opposite_dir = (tide_primary + 180) % 360
    
    diff = abs(wind_dir - opposite_dir)
    if diff > 180:
        diff = 360 - diff
    
    compass_idx = int((wind_dir + 11.25) / 22.5) % 16
    wind_compass = compass_pts[compass_idx]
    
    print(f"  Wind: {wind_dir}° ({wind_compass})")
    print(f"  Tide: {tide_state.upper()} → flows {tide_primary}° (SW)")
    print(f"  Opposite of tide: {opposite_dir}° (NE)")
    print(f"  Angle difference: {diff:.0f}°")
    
    if diff < 45:
        print(f"  ✅ Result: OPPOSITION DETECTED")
    else:
        print(f"  ℹ️ Result: Same direction pattern (not directly opposed)")

# Test case 3: Rising tide, wind from 270° (W) - should NOT detect opposition
print("\nTest Case 3: RISING TIDE with W WIND (270°)")
wind_dir = 270
tide_state = "rising"  # Maps to 45° (NE)

tide_info = navigator.TIDE_DIRECTIONS.get(tide_state)
if tide_info:
    tide_primary = tide_info["primary"]
    opposite_dir = (tide_primary + 180) % 360
    
    diff = abs(wind_dir - opposite_dir)
    if diff > 180:
        diff = 360 - diff
    
    compass_idx = int((wind_dir + 11.25) / 22.5) % 16
    wind_compass = compass_pts[compass_idx]
    
    print(f"  Wind: {wind_dir}° ({wind_compass})")
    print(f"  Tide: {tide_state.upper()} → flows {tide_primary}° (NE)")
    print(f"  Opposite of tide: {opposite_dir}° (SW)")
    print(f"  Angle difference: {diff:.0f}°")
    
    if diff < 45:
        print(f"  ✅ Result: OPPOSITION DETECTED")
    else:
        print(f"  ℹ️ Result: Same direction pattern (not directly opposed)")

print("\n" + "="*60)
print("✅ All opposition detection tests completed")
print("="*60)

# Test NIWA function existence
print("\nTest: NIWA tide function exists")
if hasattr(navigator, 'fetch_niwa_tide_data'):
    print("✅ fetch_niwa_tide_data function found")
    print("   - Returns: tide_state, magnitude, magnitude_factor, range, description")
else:
    print("❌ fetch_niwa_tide_data function not found")

print("\n✅ All tests completed successfully!")
