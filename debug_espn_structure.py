import requests
import json

def probe():
    url = "http://site.api.espn.com/apis/v2/sports/soccer/eng.1/standings"
    res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    data = res.json()
    
    if 'children' not in data:
        print("No children found")
        return

    print(f"Total Children: {len(data['children'])}")
    
    for idx, child in enumerate(data['children']):
        print(f"\n--- CHILD {idx} ---")
        print(f"Name: {child.get('name')}")
        print(f"Abbr: {child.get('abbreviation')}")
        # Check first entry's stats
        if 'standings' in child and 'entries' in child['standings']:
            entries = child['standings']['entries']
            if entries:
                print(f"Entries Count: {len(entries)}")
                first_team = entries[0]['team']['displayName']
                print(f"First Team: {first_team}")

if __name__ == "__main__":
    probe()
