#!/usr/bin/env python3
"""
Test to verify conversation memory feature.
Tests that follow-up questions use context from previous recommendations.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from navigator import get_updated_executor

def test_conversation_memory():
    """Test that the agent uses conversation context for follow-up questions."""
    print("=" * 80)
    print("Testing Conversation Memory Feature")
    print("=" * 80)
    
    executor = get_updated_executor()
    
    # Simulate first query with time recommendations
    print("\n1️⃣ INITIAL QUERY: Cook Strait crossing recommendation")
    print("-" * 80)
    query1 = "Vessel: 6m. VHF: True. PFDs: True. Question: Can I do a couple nights in the Sounds at Koamaru in the next week?"
    
    print("Running first query...")
    try:
        response1 = executor.invoke({"input": query1})
        
        # Extract key info from response (times, dates)
        output1 = response1["output"]
        print("\n✅ Got crossing recommendation")
        
        # Look for date patterns in response
        if "Friday" in output1 and "Sunday" in output1:
            print("   - Found explicit dates: Friday - Sunday")
            start_date = "Friday"
            end_date = "Sunday"
        else:
            start_date = "[date in output]"
            end_date = "[date in output]"
        
        # Extract first 300 chars of recommendation
        print(f"\n   Recommendation excerpt:\n   {output1[:300]}...")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return
    
    # Now simulate follow-up query
    print("\n\n2️⃣ FOLLOW-UP QUERY: Request moorings using previous context")
    print("-" * 80)
    
    # Simulate what app.py would do - pass context from previous response
    previous_context = f"[PREVIOUS CONTEXT: {output1[:500]}...]"
    query2 = f"Vessel: 6m. VHF: True. PFDs: True. Question: What moorings would be good for that time period?{previous_context}"
    
    print("Running follow-up query with context...")
    print(f"Query: What moorings would be good for that time period?")
    print("Context: [Previous crossing recommendation included]")
    print()
    
    try:
        response2 = executor.invoke({"input": query2})
        
        output2 = response2["output"]
        
        print("✅ Got mooring recommendations\n")
        print("Response excerpt:")
        print("-" * 80)
        print(output2[:600])
        print("...\n")
        
        # Check if agent correctly used the timeframe
        if "Friday" in output2 or "Sunday" in output2 or "Feb" in output2:
            print("✅ Agent correctly used dates from previous context!")
        elif "Friday" in output1:
            print("⚠️ Agent may not have extracted dates from context")
            print("   (Check output above to verify dates were mentioned)")
        else:
            print("❓ Could not verify date usage")
            
    except Exception as e:
        print(f"Error: {str(e)}")
    
    print("\n" + "=" * 80)
    print("Conversation Memory Test Complete")
    print("=" * 80)

if __name__ == "__main__":
    test_conversation_memory()
