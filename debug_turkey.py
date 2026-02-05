
import requests
import json
from datetime import datetime, timedelta

def check_league(league_code):
    print(f"--- CHECKING {league_code} ---")
    today = datetime.now()
    dates = [today.strftime("%Y%m%d"), (today + timedelta(days=1)).strftime("%Y%m%d")]
    
    found = False
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    for date_str in dates:
        url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{league_code}/scoreboard?dates={date_str}"
        print(f"Fetching: {url}")
        res = requests.get(url, headers=headers)
        data = res.json()
        
        league_name = data.get('leagues', [{}])[0].get('name', 'Unknown')
        print(f"League Name in API: {league_name}")
        
        events = data.get('events', [])
        print(f"Date: {date_str} | Events Found: {len(events)}")
        
        for e in events:
            name = e.get('name', 'Unknown')
            print(f"  > Match: {name} | Status: {e.get('status', {}).get('type', {}).get('state')}")
            if "Adana" in name or "Bolu" in name or "Amed" in name:
                print(f"    !!! FOUND REQUESTED TEAM: {name}")
                found = True

    return found

check_league("tur.1")
check_league("tur.2")
