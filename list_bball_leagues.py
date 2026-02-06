
import requests
import json

url = "https://sports.core.api.espn.com/v2/sports/basketball/leagues?limit=200"
res = requests.get(url)
if res.status_code == 200:
    data = res.json()
    items = data.get('items', [])
    for item in items:
        # Each item is usually a link or has a $ref
        ref = item.get('$ref', '')
        # We can try to extract the ID from the ref or fetch it
        parts = ref.split('/')
        if 'leagues' in parts:
            idx = parts.index('leagues')
            if idx + 1 < len(parts):
                code = parts[idx+1].split('?')[0]
                print(f"League Code: {code}")
else:
    print(f"Failed: {res.status_code}")
