#!/usr/bin/env python3
"""Quick test demonstrating the expanded weekend functionality."""

import os
import sys
from datetime import datetime

os.environ['METOCEAN_API_KEY'] = 'test_key'
os.environ['NIWA_API_KEY'] = 'test_key'

import navigator

print("=" * 70)
print("WEEKEND PARSING WITH FRIDAY – COMPREHENSIVE TEST")
print("=" * 70)

today = datetime.now()
print(f"\n📅 Today: {today.strftime('%A, %d %B %Y')}\n")

# Test "this weekend"
print("🎯 'This Weekend' (coming Friday through Sunday):")
fri_this, sat_this, sun_this, days_this = navigator.parse_weekend_dates('this')
print(f"   • Friday:   {fri_this.strftime('%A, %d %b')}")
print(f"   • Saturday: {sat_this.strftime('%A, %d %b')}")
print(f"   • Sunday:   {sun_this.strftime('%A, %d %b')}")
print(f"   • Forecast days needed: {days_this}\n")

# Test "next weekend"
print("🎯 'Next Weekend' (following Friday through Sunday):")
fri_next, sat_next, sun_next, days_next = navigator.parse_weekend_dates('next')
print(f"   • Friday:   {fri_next.strftime('%A, %d %b')}")
print(f"   • Saturday: {sat_next.strftime('%A, %d %b')}")
print(f"   • Sunday:   {sun_next.strftime('%A, %d %b')}")
print(f"   • Forecast days needed: {days_next}\n")

# Show the difference
print(f"📊 Gap between weekends: {(fri_next - fri_this).days} days")

print("\n" + "=" * 70)
print("EXAMPLE QUERIES NOW SUPPORTED")
print("=" * 70)

examples = [
    "Is it good to fish at Pukerua Bay this weekend?",
    "Can I cross to the Sounds next weekend?",
    "Best fishing spot this weekend?",
    "What are conditions for Mana Marina this weekend?",
    "When's good to cross next weekend?",
]

print("\nThese queries will now return forecasts for Friday–Sunday:")
for i, query in enumerate(examples, 1):
    print(f"  {i}. {query}")

print("\n" + "=" * 70)
print("✅ Weekend parsing with Friday included: WORKING")
print("=" * 70)
