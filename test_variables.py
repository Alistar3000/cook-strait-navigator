import os
from dotenv import load_dotenv
import requests
import json

load_dotenv()
api_key = os.getenv('METOCEAN_API_KEY')

print("Testing variable combinations...\n")

test_cases = [
    "wind.speed.at-10m,wind.direction.at-10m,wave.height",
    "wind.speed.at-10m,wave.height,tide.surface",
    "wind.speed.at-10m,wave.height,tide.current.speed",
    "wind.speed.at-10m,wave.height",
]

for variables in test_cases:
    params = {
        'lat': -41.35,
        'lon': 174.87,
        'variables': variables,
        'from': '2026-02-19T00:00:00Z',
        'to': '2026-02-21T00:00:00Z'
    }
    
    r = requests.get('https://forecast-v2.metoceanapi.com/point/time', 
                     params=params, 
                     headers={'x-api-key': api_key}, 
                     verify=False)
    
    print(f"Variables: {variables}")
    print(f"Status: {r.status_code}")
    
    if r.status_code == 200:
        data = r.json()
        available = list(data.get('variables', {}).keys())
        print(f"✅ SUCCESS - Got: {available}\n")
    else:
        print(f"❌ Error: {r.text[:150]}\n")
