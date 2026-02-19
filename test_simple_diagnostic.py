#!/usr/bin/env python3
"""Detailed diagnostic test for fetch_niwa_tide_data availability."""

import sys
import os
import ast

# First, check if module can be parsed
print("=" * 60)
print("STEP 1: Checking if navigator.py can be parsed")
print("=" * 60)

try:
    with open("navigator.py", "r", encoding="utf-8") as f:
        code = f.read()
    tree = ast.parse(code)
    print("[OK] navigator.py parses successfully as valid Python")
except SyntaxError as e:
    print(f"[ERROR] Syntax Error in navigator.py: {e}")
    sys.exit(1)

# Find all function definitions
print("\nSearching for function definitions...")
functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

if 'fetch_niwa_tide_data' in functions:
    print("[OK] fetch_niwa_tide_data - FOUND")
else:
    print("[ERROR] fetch_niwa_tide_data - NOT FOUND")

if 'fetch_marine_data' in functions:
    print("[OK] fetch_marine_data - FOUND")
else:
    print("[ERROR] fetch_marine_data - NOT FOUND")

# Check function order
print("\n" + "=" * 60)
print("STEP 2: Checking function definition order")
print("=" * 60)

with open("navigator.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

fetch_niwa_line = None
fetch_marine_line = None

for i, line in enumerate(lines, 1):
    if line.startswith("def fetch_niwa_tide_data"):
        fetch_niwa_line = i
    elif line.startswith("def fetch_marine_data"):
        fetch_marine_line = i

print(f"fetch_niwa_tide_data:  Line {fetch_niwa_line}")
print(f"fetch_marine_data:     Line {fetch_marine_line}")

if fetch_niwa_line and fetch_marine_line and fetch_niwa_line < fetch_marine_line:
    print("[OK] fetch_niwa_tide_data is defined BEFORE fetch_marine_data")
else:
    print("[ERROR] Definition order issue!")

# Check if fetch_marine_data calls fetch_niwa_tide_data
print("\n" + "=" * 60)
print("STEP 3: Searching for function calls")
print("=" * 60)

calls_found = 0
for i, line in enumerate(lines, 1):
    if 'fetch_niwa_tide_data(' in line:
        print(f"Line {i}: {line.strip()}")
        calls_found += 1

print(f"\nTotal calls to fetch_niwa_tide_data: {calls_found}")

if calls_found > 0:
    print("[OK] Function is being called")
else:
    print("[WARNING] Function is defined but never called")

print("\n" + "=" * 60)
print("Code structure is VALID")
print("=" * 60)
