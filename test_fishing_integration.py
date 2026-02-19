#!/usr/bin/env python3
"""Quick test of fishing report integration"""

from navigator import search_fishing_reports, search_books

print("="*60)
print("TESTING FISHING REPORT Integration")
print("="*60)

# Test 1: Query for snapper with light northerlies
print("\n1. Testing fishing report query: 'snapper light northerlies'")
result = search_fishing_reports("snapper light northerlies")
print(result)

# Test 2: Query for Pukerua Bay
print("\n2. Testing fishing report query: 'Pukerua Bay'")
result = search_fishing_reports("Pukerua Bay")
print(result)

# Test 3: Test maritime knowledge still works
print("\n3. Testing maritime knowledge query: 'dangerous rips'")
result = search_books("dangerous rips")
print(result)

print("\n" + "="*60)
print("Integration test complete!")
print("="*60)
