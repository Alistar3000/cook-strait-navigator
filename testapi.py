# test_api3.py - Find correct variable names
import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

api_key = os.getenv("METOCEAN_API_KEY")
lat = -41.2145
lon = 174.3212
now_dt = datetime.now()

# Try different variable name formats
variable_tests = [
    "wind_speed,wave_height",
    "wind_speed_10m,sea_surface_wave_significant_height",
    "wind.speed.at-10m,wave.height",
    "windSpeed,waveHeight",
    "wind,wave"
]

url = "https://forecast-v2.metoceanapi.com/point/time"

for variables in variable_tests:
    print(f"\n{'='*60}")
    print(f"Testing variables: {variables}")
    print(f"{'='*60}")
    
    params = {
        "lat": lat,
        "lon": lon,
        "variables": variables,
        "from": now_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "to": (now_dt + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    try:
        r = requests.get(
            url, 
            params=params, 
            headers={"x-api-key": api_key},
            verify=False,
            timeout=10
        )
        
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            print(f"✅✅✅ SUCCESS! ✅✅✅")
            print(f"Variables returned: {list(data.get('variables', {}).keys())}")
            print(f"Number of time points: {len(data.get('dimensions', {}).get('time', []))}")
            
            # Show first few data points
            for var_name, var_data in data.get('variables', {}).items():
                data_array = var_data.get('data', [])
                if data_array:
                    print(f"  {var_name}: First value = {data_array[0]}")
            
            print(f"\n🎉 USE THESE VARIABLES: {variables}")
            break
        else:
            print(f"❌ Error: {r.text[:200]}")
    except Exception as e:
        print(f"❌ Exception: {e}")

print(f"\n{'='*60}")
print("Test complete")