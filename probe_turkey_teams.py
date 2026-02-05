import requests
import json
import sys

def search_teams():
    # ESPN Team Search doesn't have a direct "search" endpoint, 
    # but we can try to find them by probing common IDs or finding them in league data.
    
    leagues = ["tur.1", "tur.2", "tur.cup"]
    targets = ["Adana", "Besiktas", "Bolu", "Amed", "Demirspor", "Samsun"]
    
    print("--- SEARCHING FOR TURKISH TEAMS IN LEAGUE DATA ---")
    
    for league in leagues:
        url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{league}/teams"
        try:
            res = requests.get(url, timeout=5).json()
            teams = res.get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', [])
            print(f"\n[{league}] Found {len(teams)} teams")
            for t in teams:
                t_info = t.get('team', {})
                name = t_info.get('displayName', '')
                if any(x.lower() in name.lower() for x in targets):
                    print(f"  MATCH: {name} (ID: {t_info.get('id')})")
        except:
            print(f"[{league}] Failed to fetch teams")

    # Also try to search for the match specifically via a search query if we can find an endpoint.
    # But let's check global scoreboard again with a higher limit.
    print("\n--- PROBING GLOBAL SCOREBOARD WITH HIGH LIMIT ---")
    today = "20260201"
    url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/scoreboard?dates={today}&limit=1000"
    try:
        res = requests.get(url, timeout=5).json()
        events = res.get('events', [])
        print(f"Global soccer events (limit 1000): {len(events)}")
        for e in events:
            name = e.get('name', '')
            if any(x.lower() in name.lower() for x in targets):
                print(f"  FOUND: {name} | League: {e.get('season', {}).get('name')}")
    except:
        print("Global scoreboard failed")

if __name__ == '__main__':
    search_teams()
