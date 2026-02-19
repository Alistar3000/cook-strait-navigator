#!/usr/bin/env python3
"""
Test to verify that the agent correctly classifies query types.
Tests that fishing queries are no longer misidentified as Cook Strait crossing queries.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from navigator import get_updated_executor

def test_fishing_query_classification():
    """Test that fishing queries are properly classified."""
    print("=" * 80)
    print("Testing Query Classification Fix")
    print("=" * 80)
    
    executor = get_updated_executor()
    
    # Test case 1: Fishing days query (the problematic case from the user report)
    print("\n❓ TEST 1: Fishing days query")
    print("-" * 80)
    query1 = "Vessel: 6m. VHF: True. PFDs: True. Question: Are there any decent fishing days coming up in the next week?"
    print(f"Query: {query1}")
    print("\nExpected: Should classify as TYPE 3 (BEST TIME ANALYSIS) and analyze fishing conditions")
    print("NOT as Cook Strait crossing to Cape Koamaru\n")
    
    try:
        response1 = executor.invoke({"input": query1})
        print("Response from agent:")
        print("-" * 80)
        print(response1["output"][:500])  # Print first 500 chars
        print("\n✅ Did the agent correctly identify this as a fishing query?")
        if "fishing" in response1["output"].lower() and "cape koamaru" not in response1["output"].lower():
            print("   YES - Agent correctly routed to fishing analysis")
        elif "cape koamaru" in response1["output"].lower():
            print("   ❌ NO - Agent still misrouting to Cook Strait crossing")
        else:
            print("   ? UNCLEAR - Check output above")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Test case 2: Entrance-only query (should still work for Cook Strait)
    print("\n\n❓ TEST 2: Entrance-only query (follow-up)")
    print("-" * 80)
    query2 = "Vessel: 6m. VHF: True. PFDs: True. Question: Koamaru"
    print(f"Query: {query2}")
    print("\nExpected: Should classify as entrance-only follow-up to Cook Strait crossing")
    print("Should proceed with weather checks for Cape Koamaru from Mana Marina\n")
    
    try:
        response2 = executor.invoke({"input": query2})
        print("Response from agent:")
        print("-" * 80)
        print(response2["output"][:500])  # Print first 500 chars
        print("\n✅ Did the agent correctly identify this as entrance-only?")
        if "crossing" in response2["output"].lower() or "mana marina" in response2["output"].lower():
            print("   YES - Agent correctly routed to Cook Strait crossing")
        else:
            print("   ❌ NO - Agent may have misclassified")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Test case 3: Sounds without entrance (should ask for clarification)
    print("\n\n❓ TEST 3: Sounds without entrance (needs clarification)")
    print("-" * 80)
    query3 = "Vessel: 6m. VHF: True. PFDs: True. Question: Can I safely cross to the Marlborough Sounds this weekend?"
    print(f"Query: {query3}")
    print("\nExpected: Should ask which entrance (Tory or Koamaru)")
    print("Should NOT immediately provide forecast\n")
    
    try:
        response3 = executor.invoke({"input": query3})
        print("Response from agent:")
        print("-" * 80)
        print(response3["output"][:500])  # Print first 500 chars
        print("\n✅ Did the agent correctly ask for entrance clarification?")
        if "which entrance" in response3["output"].lower() or "tory" in response3["output"].lower():
            print("   YES - Agent correctly asked for entrance specification")
        else:
            print("   ❌ NO - Agent may have skipped clarification")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    print("\n" + "=" * 80)
    print("Query Classification Tests Complete")
    print("=" * 80)

if __name__ == "__main__":
    test_fishing_query_classification()
