import requests
import json

def fetch_espn_scores(league_code, sport="soccer"):
    url = f"http://site.api.espn.com/apis/site/v2/sports/{sport}/{league_code}/scoreboard"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=5)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"Error fetching {league_code}: {e}")
        return None

data = fetch_espn_scores("eng.1", "soccer")
if data and 'events' in data:
    for event in data['events']:
        competitors = event.get('competitions', [{}])[0].get('competitors', [])
        
        print("\n--- MATCH FOUND: " + event.get('name', 'Unknown') + " ---")
        for c in competitors:
            stats = c.get('statistics', [])
            print(f"Team: {c.get('team', {}).get('name')}")
            for s in stats:
                print(f"Stat: {s.get('name')} | Abbr: {s.get('abbreviation')} | Val: {s.get('displayValue')}")
        break  # Just need one match
