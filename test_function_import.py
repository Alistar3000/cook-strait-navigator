#!/usr/bin/env python3
"""Test if fetch_niwa_tide_data function is accessible."""

import os
import sys

# Set dummy keys
os.environ['METOCEAN_API_KEY'] = 'test'
os.environ['NIWA_API_KEY'] = 'test'

try:
    from navigator import fetch_niwa_tide_data, fetch_weather_wrapper
    print("✅ Successfully imported fetch_niwa_tide_data")
    print(f"  Function location: {fetch_niwa_tide_data.__module__}.{fetch_niwa_tide_data.__name__}")
    print(f"  Callable: {callable(fetch_niwa_tide_data)}")
    print("\n✅ Successfully imported fetch_weather_wrapper")
    print(f"  Function location: {fetch_weather_wrapper.__module__}.{fetch_weather_wrapper.__name__}")
    print(f"  Callable: {callable(fetch_weather_wrapper)}")
except ImportError as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
except NameError as e:
    print(f"❌ Name error: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
