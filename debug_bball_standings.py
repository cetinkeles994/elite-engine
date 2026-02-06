
import requests
import json

# EuroLeague: mens-euroleague
# BSL: mens-turkish-super-league

def check_league(league, season):
    URL = f"https://site.api.espn.com/apis/v2/sports/basketball/{league}/standings?season={season}"
    print(f"\nFetching: {league} - Season {season}")
    try:
        resp = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        if resp.status_code != 200:
            print(f"Failed with {resp.status_code}")
            return
            
        data = resp.json()
        
        if 'children' in data:
            print(f"Children Count: {len(data['children'])}")
            if data['children']:
                print(f"First Child Entries: {len(data['children'][0].get('standings', {}).get('entries', []))}")
        elif 'standings' in data:
             print(f"Root Entries: {len(data['standings'].get('entries', []))}")
        else:
            print("No standings data found.")
            
    except Exception as e:
        print(f"Error: {e}")

leagues = ['mens-euroleague', 'mens-turkish-super-league', 'nba']
seasons = [2025, 2024, 2026]

for l in leagues:
    for s in seasons:
        check_league(l, s)
