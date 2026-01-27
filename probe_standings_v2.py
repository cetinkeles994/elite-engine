import requests
import json

# Try to fetch standings for EPL (eng.1) to find GF/GA stats
url = "http://site.api.espn.com/apis/v2/sports/soccer/eng.1/standings"
print(f"Fetching {url}...")

try:
    res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    data = res.json()
    
    # Save for inspection
    with open("debug_standings.json", "w") as f:
        json.dump(data, f, indent=2)
        
    print("Saved debug_standings.json")
    
    if 'children' in data:
        print("Found Children (Groups/Seasons)...")
        standings = data['children'][0]['standings']['entries']
        print(f"Found {len(standings)} teams.")
        
        # Analyze first team to find GF/GA
        team1 = standings[0]
        print(f"Team: {team1['team']['displayName']}")
        for stat in team1['stats']:
            # 'pointsFor' usually Goals For, 'pointsAgainst' usually Goals Against
            if stat['name'] in ['pointsFor', 'pointsAgainst', 'goalDifference', 'gamesPlayed']:
                print(f"  - {stat['name']}: {stat['value']}")

except Exception as e:
    print(f"Error: {e}")
