import os
from dotenv import load_dotenv
import requests

load_dotenv()
api_key = os.getenv('NIWA_API_KEY')

print(f'Testing different authentication approaches...\n')

params = {
    'lat': -41.2,
    'lon': 174.55,
    'start_date': '2026-02-19',
    'end_date': '2026-02-20'
}

# Try 1: api_key as query parameter
params_with_key = {**params, 'api_key': api_key}
r = requests.get('https://api.niwa.co.nz/tides/data', params=params_with_key)
print(f'Test 1 (api_key in params): {r.status_code}')
try:
    data = r.json()
    if 'data' in data:
        print(f'  SUCCESS! Got {len(data["data"])} data points')
        print(f'  Sample: {data["data"][0]}')
    else:
        print(f'  Response keys: {list(data.keys())}')
except:
    print(f'  Error: {r.text[:200]}')

# Try 2: apikey (no x-) header
print()
headers2 = {'apikey': api_key}
r = requests.get('https://api.niwa.co.nz/tides/data', params=params, headers=headers2)
print(f'Test 2 (apikey header): {r.status_code}')
try:
    data = r.json()
    if 'data' in data:
        print(f'  SUCCESS! Got {len(data["data"])} data points')
    else:
        print(f'  Response: {data}')
except:
    print(f'  Error: {r.text[:200]}')

# Try 3: Check if there's a documentation page
print()
r = requests.get('https://api.niwa.co.nz/tides')
print(f'Test 3 (base /tides endpoint): {r.status_code}')
if 'html' in r.text.lower():
    print(f'  Returns HTML (documentation page)')
else:
    print(f'  Response preview: {r.text[:200]}')
