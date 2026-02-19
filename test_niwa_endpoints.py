import os
from dotenv import load_dotenv
import requests

load_dotenv()
api_key = os.getenv("NIWA_API_KEY")

# Test different endpoint variations based on NIWA docs
endpoints = [
    "https://api.niwa.co.nz/tide/data",
    "https://api.niwa.co.nz/v1/tide/data",
    "https://api.niwa.co.nz/tides/data",
    "https://api.niwa.co.nz/data/tide",
]

params = {
    "lat": -41.2,
    "lon": 174.55,
    "start_date": "2026-02-19",
    "end_date": "2026-02-20"
}

headers = {"x-api-key": api_key}

for endpoint in endpoints:
    print(f"\n=== Testing: {endpoint} ===")
    try:
        r = requests.get(endpoint, params=params, headers=headers, timeout=5)
        print(f"Status: {r.status_code}")
        
        # Check if JSON
        try:
            data = r.json()
            print(f"✓ Valid JSON - Keys: {list(data.keys())[:5]}")
        except:
            # Check content type
            content_type = r.headers.get('content-type', 'unknown')
            if 'json' in content_type.lower():
                print(f"Content-Type: {content_type}")
                print(f"Response preview: {r.text[:100]}")
            else:
                is_html = '<html' in r.text.lower()
                print(f"Not JSON - HTML: {is_html}")
                if not is_html:
                    print(f"Response preview: {r.text[:100]}")
    except Exception as e:
        print(f"Error: {e}")
