import requests
import json

def probe():
    url = "http://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard"
    res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    data = res.json()
    
    events = data.get('events', [])
    if not events:
        print("No events found.")
        return

    # Check first match
    event = events[0]
    print(f"Match: {event['name']}")
    
    comps = event['competitions'][0]['competitors']
    
    for c in comps:
        print(f"\nTeam: {c['team']['name']} ({c['homeAway']})")
        records = c.get('records', [])
        for r in records:
            print(f" - Type: {r.get('type')} | Summary: {r.get('summary')}")

if __name__ == "__main__":
    probe()
