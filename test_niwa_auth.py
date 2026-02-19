import os
from dotenv import load_dotenv
import requests
import json

load_dotenv()
api_key = os.getenv('NIWA_API_KEY')
api_secret = os.getenv('NIWA_API_SECRET')

print(f'Testing /tides/data endpoint with variations...\n')

params = {
    'lat': -41.2,
    'lon': 174.55,
    'start_date': '2026-02-19',
    'end_date': '2026-02-20'
}

# Try 1: x-api-key only
headers1 = {'x-api-key': api_key}
r = requests.get('https://api.niwa.co.nz/tides/data', params=params, headers=headers1)
print(f'Test 1 (x-api-key only): {r.status_code}')
if r.status_code == 200:
    data = r.json()
    print(f'  Has data key: {"data" in data}')
    if 'data' in data:
        print(f'  Data points: {len(data["data"])}')
        print(f'  Sample: {data["data"][0]}')
else:
    print(f'  Error: {r.json()}')

# Try 2: x-api-key and x-api-secret
print()
headers2 = {'x-api-key': api_key, 'x-api-secret': api_secret}
r = requests.get('https://api.niwa.co.nz/tides/data', params=params, headers=headers2)
print(f'Test 2 (with x-api-secret): {r.status_code}')
if r.status_code == 200:
    data = r.json()
    print(f'  Has data key: {"data" in data}')
    if 'data' in data:
        print(f'  Data points: {len(data["data"])}')
        print(f'  Sample: {data["data"][0]}')
else:
    print(f'  Error: {r.json()}')
