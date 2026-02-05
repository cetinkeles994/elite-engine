import requests
import json

def probe():
    url = "http://site.api.espn.com/apis/v2/sports/soccer/eng.1/standings"
    res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    data = res.json()
    
    if 'children' not in data:
        print("No children found")
        return

    # Check first team
    entry = data['children'][0]['standings']['entries'][0]
    print(f"Team: {entry['team']['displayName']}")
    
    print("\n--- STATS ---")
    for s in entry['stats']:
        print(f"Stat: {s['name']} | Val: {s.get('value')} | Desc: {s.get('description')}")
        
    # Check for splits (often in a different structure or implied)
    # Sometimes 'splits' is a separate list in the response

if __name__ == "__main__":
    probe()
