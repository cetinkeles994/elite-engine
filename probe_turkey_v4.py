import requests
import json
import sys
import codecs

# Force UTF-8 for Windows console
if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

def probe_league(code):
    url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard?dates=20260201"
    print(f"--- PROBING: {code} ---")
    try:
        res = requests.get(url, timeout=5)
        if res.status_code != 200:
            print(f"  FAILED: Status {res.status_code}")
            return
        data = res.json()
        
        leagues = data.get('leagues', [])
        if leagues:
            print(f"  League Name in API: {leagues[0].get('name')}")
        
        events = data.get('events', [])
        print(f"  Events Found: {len(events)}")
        for e in events:
            name = e.get('name')
            comp = e.get('competitions', [{}])[0]
            comp_type = comp.get('type', {}).get('name', 'N/A')
            status = e.get('status', {}).get('type', {}).get('detail', 'N/A')
            print(f"    - Match: {name} | Comp: {comp_type} | Status: {status}")
            
    except Exception as e:
        print(f"  ERROR: {e}")

def search_teams():
    url = "http://site.api.espn.com/apis/site/v2/sports/soccer/scoreboard?dates=20260201"
    print("\n--- SEARCHING FOR TARGET TEAMS IN GLOBAL SCOREBOARD ---")
    try:
        res = requests.get(url, timeout=5)
        data = res.json()
        for e in data.get('events', []):
            name = e.get('name')
            if any(x in name for x in ["Adana", "Besiktas", "Beşiktaş", "Bolu", "Amed", "Demirspor"]):
                print(f"  !!! FOUND: {name}")
                league_info = e.get('season', {}) # Sometimes has league info
                print(f"      Data: {name}")
    except Exception as e:
        print(f"  ERROR: {e}")

codes = ["tur.1", "tur.2", "tur.3", "tur.cup", "tur.super_cup", "tur.super", "tur.league"]
for c in codes:
    probe_league(c)

search_teams()
