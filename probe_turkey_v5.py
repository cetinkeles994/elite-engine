import requests
import json
import sys

def probe(date_str="20260201"):
    print(f"--- TARGETED PROBE FOR {date_str} ---")
    
    # 1. Check Global Soccer for keywords
    global_url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/scoreboard?dates={date_str}&limit=200"
    try:
        res = requests.get(global_url, timeout=10)
        data = res.json()
        print(f"Global soccer events: {len(data.get('events', []))}")
        for e in data.get('events', []):
            name = e.get('name', '')
            if any(x.lower() in name.lower() for x in ["Adana", "Besiktas", "Bolu", "Amed", "Demirspor"]):
                print(f"[FOUND GLOBAL] {name}")
                print(f"  League: {e.get('season', {}).get('name', 'N/A')} | ID: {e.get('league', {}).get('id', 'N/A')}")
    except Exception as ex:
        print(f"Global probe error: {ex}")

    # 2. Check specific codes
    for code in ["tur.1", "tur.2", "tur.cup"]:
        url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard?dates={date_str}"
        try:
            res = requests.get(url, timeout=5)
            d = res.json()
            league_name = d.get('leagues', [{}])[0].get('name', 'Unknown')
            events = d.get('events', [])
            print(f"\n[{code}] {league_name} - {len(events)} events")
            for ev in events:
                print(f"  - {ev.get('name')}")
        except Exception as ex:
            print(f"[{code}] Error: {ex}")

if __name__ == '__main__':
    probe()
