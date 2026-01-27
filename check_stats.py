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
        competitions = event.get('competitions', [{}])[0]
        competitors = competitions.get('competitors', [])
        
        print("\n--- MATCH FOUND: " + event.get('name', 'Unknown') + " ---")
        for c in competitors:
            print(f"Team: {c.get('team', {}).get('name')}")
            print(f"Scores: {c.get('score')}")
            # Check for interesting keys
            print(f"Competitor Keys: {list(c.keys())}")
            # Check for statistics
            if 'statistics' in c:
                print(f"Statistics found: {c['statistics']}")
            else:
                print("No statistics found in competitor object.")
            
            # Check linescores for periods
            if 'linescores' in c:
                 print(f"Linescores: {c['linescores']}")
        break
else:
    print("No events found or API error.")
