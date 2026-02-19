import os
from dotenv import load_dotenv
import requests

load_dotenv()
api_key = os.getenv('METOCEAN_API_KEY')

# Test common tide variable name patterns
test_vars = [
    'tide.surface_elevation',
    'tide.water_level', 
    'sea_surface_height',
    'water_surface_elevation',
    'tide.msl',
    'sea.surface.height',
]

for var in test_vars:
    params = {
        'lat': -41.35,
        'lon': 174.87,
        'variables': var,
        'from': '2026-02-19T00:00:00Z',
        'to': '2026-02-19T12:00:00Z'
    }
    
    r = requests.get('https://forecast-v2.metoceanapi.com/point/time',
                     params=params,
                     headers={'x-api-key': api_key},
                     verify=False)
    
    status = "WORKS" if r.status_code == 200 else f"ERROR {r.status_code}"
    print(f"{var}: {status}")
