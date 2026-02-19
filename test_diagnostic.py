#!/usr/bin/env python3
"""Detailed diagnostic test for fetch_niwa_tide_data availability."""

import sys
import os

# First, check if module can be parsed
print("=" * 60)
print("STEP 1: Checking if navigator.py can be parsed")
print("=" * 60)

try:
    import ast
    with open("navigator.py", "r", encoding="utf-8") as f:
        code = f.read()
    tree = ast.parse(code)
    print("✅ navigator.py parses successfully as valid Python")
except SyntaxError as e:
    print(f"❌ Syntax Error in navigator.py: {e}")
    sys.exit(1)

# Find all function definitions
print("\nSearching for function definitions...")
functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
print(f"Found {len(functions)} functions:")

if 'fetch_niwa_tide_data' in functions:
    print("  ✅ fetch_niwa_tide_data - FOUND")
else:
    print("  ❌ fetch_niwa_tide_data - NOT FOUND")

if 'fetch_marine_data' in functions:
    print("  ✅ fetch_marine_data - FOUND")
else:
    print("  ❌ fetch_marine_data - NOT FOUND")

if 'fetch_weather_wrapper' in functions:
    print("  ✅ fetch_weather_wrapper - FOUND")
else:
    print("  ❌ fetch_weather_wrapper - NOT FOUND")

# Check function order
print("\n" + "=" * 60)
print("STEP 2: Checking function definition order")
print("=" * 60)

with open("navigator.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

fetch_niwa_line = None
fetch_marine_line = None
fetch_weather_line = None

for i, line in enumerate(lines, 1):
    if line.startswith("def fetch_niwa_tide_data"):
        fetch_niwa_line = i
    elif line.startswith("def fetch_marine_data"):
        fetch_marine_line = i
    elif line.startswith("def fetch_weather_wrapper"):
        fetch_weather_line = i

print(f"fetch_niwa_tide_data:  Line {fetch_niwa_line}")
print(f"fetch_marine_data:     Line {fetch_marine_line}")
print(f"fetch_weather_wrapper: Line {fetch_weather_line}")

if fetch_niwa_line and fetch_marine_line and fetch_niwa_line < fetch_marine_line:
    print("\n✅ fetch_niwa_tide_data is defined BEFORE fetch_marine_data (GOOD)")
else:
    print("\n❌ Definition order issue!")

# Check if fetch_marine_data calls fetch_niwa_tide_data
print("\n" + "=" * 60)
print("STEP 3: Searching for function calls")
print("=" * 60)

fetch_marine_start = fetch_marine_line - 1
fetch_marine_end = None

# Find the end of fetch_marine_data function
for i in range(fetch_marine_start, len(lines)):
    if i > fetch_marine_start and lines[i][0] not in [' ', '\t'] and lines[i].strip():
        fetch_marine_end = i
        break

if not fetch_marine_end:
    fetch_marine_end = len(lines)

print(f"fetch_marine_data spans lines {fetch_marine_start + 1}-{fetch_marine_end}")

calls_in_fetch_marine = 0
for i in range(fetch_marine_start, fetch_marine_end):
    if 'fetch_niwa_tide_data(' in lines[i]:
        calls_in_fetch_marine += 1
        print(f"  Line {i + 1}: {lines[i].strip()}")

if calls_in_fetch_marine > 0:
    print(f"\n✅ fetch_niwa_tide_data is called {calls_in_fetch_marine} time(s) in fetch_marine_data")
else:
    print("\n❌ fetch_niwa_tide_data is NOT called in fetch_marine_data")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("If all checks above show ✅, then the code structure is correct.")
print("If you're still getting a NameError, the issue is likely:")
print("  1. Environment/import issue (missing dependencies)")
print("  2. Caching issue (clear __pycache__)")
print("  3. Running on Streamlit Cloud that hasn't redeployed")
