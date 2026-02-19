import os
from dotenv import load_dotenv
import requests

load_dotenv()
api_key = os.getenv("NIWA_API_KEY")
api_secret = os.getenv("NIWA_API_SECRET")

print(f"API Key: {api_key[:20]}...")
print(f"API Secret: {api_secret[:10]}...")

# Test NIWA Tide API
url = "https://api.niwa.co.nz/tide/data"

params = {
    "lat": -41.2,
    "lon": 174.55,
    "start_date": "2026-02-19",
    "end_date": "2026-02-20"
}

# Try different header approaches
print("\n=== Test 1: x-api-key header ===")
headers1 = {"x-api-key": api_key}
r = requests.get(url, params=params, headers=headers1)
print(f"Status: {r.status_code}")
print(f"Response (first 300 chars): {r.text[:300]}")

print("\n=== Test 2: Authorization header ===")
headers2 = {"Authorization": f"Bearer {api_key}"}
r = requests.get(url, params=params, headers=headers2)
print(f"Status: {r.status_code}")
print(f"Response (first 300 chars): {r.text[:300]}")

print("\n=== Test 3: Check if it's HTML (possibly error page) ===")
if "<html" in r.text.lower():
    print("Got HTML response - API might be returning error page")
    print(f"Full response:\n{r.text[:500]}")
