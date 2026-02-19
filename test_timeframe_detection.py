#!/usr/bin/env python3
"""
Test to verify that the agent correctly handles timeframe-based queries.
Tests that "in the next week" type queries pull extended forecasts.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from navigator import get_updated_executor

def test_timeframe_detection():
    """Test that timeframe queries use extended forecasts."""
    print("=" * 80)
    print("Testing Timeframe Detection for Extended Forecasts")
    print("=" * 80)
    
    executor = get_updated_executor()
    
    # Test case: Crossing with timeframe
    print("\n❓ TEST: Cook Strait crossing with 'next week' timeframe")
    print("-" * 80)
    query = "Vessel: 6m. VHF: True. PFDs: True. Question: Can I do a couple of nights in the Sounds at Koamaru in the next week?"
    print(f"Query: {query}")
    print("\nExpected: Should fetch 7-day extended forecast (not just 2 days)")
    print("Should show weather for multiple days to identify best windows\n")
    
    try:
        response = executor.invoke({"input": query})
        output = response["output"]
        
        # Check if it's looking at multiple days
        print("Response excerpt:")
        print("-" * 80)
        
        # Look for evidence of extended forecast
        if "7 day" in output.lower() or "week" in output.lower():
            print("✅ Agent correctly recognized week-long timeframe")
        else:
            print("❓ Check output below to verify timeframe was detected")
        
        # Print first 1000 chars of output
        print(output[:1000])
        print("...")
        
        # Count how many days are represented
        day_count = sum(1 for day in ["[Fri", "[Sat", "[Sun", "[Mon", "[Tue", "[Wed", "[Thu"] 
                       if day in output)
        print(f"\n📊 Days represented in forecast: ~{day_count} days")
        
        if day_count >= 5:
            print("✅ Extended forecast detected (multiple days)")
        elif day_count <= 2:
            print("❌ Only short forecast (2 days) - timeframe not applied")
        else:
            print("⚠️ Partial forecast")
            
    except Exception as e:
        print(f"Error: {str(e)}")
    
    print("\n" + "=" * 80)
    print("Timeframe Detection Test Complete")
    print("=" * 80)

if __name__ == "__main__":
    test_timeframe_detection()
