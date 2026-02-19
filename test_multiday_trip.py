#!/usr/bin/env python3
"""
Test to verify multi-day trip planning feature.
Tests that the agent properly plans 2-night, 3-day trips.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from navigator import get_updated_executor

def test_multiday_trip():
    """Test that the agent correctly plans multi-day stays."""
    print("=" * 80)
    print("Testing Multi-Day Trip Planning")
    print("=" * 80)
    
    executor = get_updated_executor()
    
    print("\n❓ TEST: 2-night trip to Koamaru next week")
    print("-" * 80)
    query = "Vessel: 6m. VHF: True. PFDs: True. Question: I'd like a 2 night trip to the Sounds at Koamaru in the next week. What days work best?"
    print(f"Query: {query}")
    print("\nExpected:")
    print("  - Should find a 3-day window (depart day + 2 anchor days + return day)")
    print("  - Depart day must be SAFE for crossing")
    print("  - Intermediate days can be CAUTION (acceptable for anchoring)")
    print("  - Return day must be SAFE for crossing")
    print("  - Show full itinerary with day-by-day breakdown")
    print("  - Should NOT recommend same-day return\n")
    
    try:
        response = executor.invoke({"input": query})
        
        output = response["output"]
        print("Response:")
        print("-" * 80)
        
        # Print key parts
        if "DAY 1" in output or "ITINERARY" in output:
            print("✅ Agent provided DAY-BY-DAY itinerary")
        else:
            print("❌ Agent did NOT provide day-by-day breakdown")
        
        # Check for multiple days
        day_count = sum(1 for day in ["DAY 1", "DAY 2", "DAY 3", "Friday", "Saturday", "Sunday"] 
                       if day in output)
        print(f"   Days mentioned: {day_count}")
        
        # Check for return dates that are NOT same-day
        if "Return" in output and ("Sunday" in output or "Monday" in output):
            print("✅ Agent recommended return on a different day (not same-day)")
        else:
            print("❓ Check output for return day recommendation")
        
        # Check for anchor day warnings
        if "Anchor" in output or "Friday" in output or "Saturday" in output:
            print("✅ Agent mentioned anchoring conditions")
        else:
            print("❓ Check if anchoring is mentioned")
        
        # Print excerpt of output
        print("\nOutput excerpt:")
        print(output[:1200])
        print("\n...")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    
    print("\n" + "=" * 80)
    print("Multi-Day Trip Test Complete")
    print("=" * 80)

if __name__ == "__main__":
    test_multiday_trip()
