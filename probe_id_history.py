import requests
import json

def find_id_history():
    # Probe a date in 2025 where Adana Demirspor definitely played.
    # Say, Jan 5, 2025.
    date_str = "20250105"
    url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/scoreboard?dates={date_str}&limit=1000"
    
    print(f"Searching for Adana Demirspor in history: {date_str}...")
    try:
        res = requests.get(url, timeout=5).json()
        events = res.get('events', [])
        print(f"Global events found: {len(events)}")
        for e in events:
            name = e.get('name', '')
            if "Adana" in name or "Demirspor" in name or "Sivas" in name or "Hatay" in name:
                print(f"  FOUND: {name}")
                competitors = e.get('competitions', [{}])[0].get('competitors', [])
                for c in competitors:
                    print(f"    Team: {c['team']['displayName']} | ID: {c['team']['id']}")
                league_id = e.get('league', {}).get('id', 'N/A')
                print(f"    League ID: {league_id}")
    except:
        print("History probe failed")

if __name__ == '__main__':
    find_id_history()
