import requests
import json

def probe_standings():
    # Premier League Standings
    url = "http://site.api.espn.com/apis/v2/sports/soccer/eng.1/standings"
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        data = res.json()
        
        # Check first team's stats
        if data.get('children'):
            standings = data['children'][0]['standings']['entries']
            print(f"Found {len(standings)} teams.")
            # Print first team details (stats like GF, GA, Wins, etc.)
            print(json.dumps(standings[0], indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    probe_standings()
