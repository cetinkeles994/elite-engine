import requests
import json

def fetch_espn_scores(league_code, sport="basketball"):
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

data = fetch_espn_scores("nba", "basketball")
if data and 'events' in data:
    for event in data['events']:
        competitions = event.get('competitions', [{}])[0]
        competitors = competitions.get('competitors', [])
        
        print("\n--- MATCH FOUND: " + event.get('name', 'Unknown') + " ---")
        for c in competitors:
            team = c.get('team', {}).get('name')
            records = c.get('records', [])
            print(f"Team: {team}")
            print(f"Records: {records}")
            
else:
    print("No events found or API error.")
