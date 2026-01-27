import requests
from datetime import datetime, timedelta

LEAGUES = [
    {"name": "Premier League", "code": "eng.1", "sport": "soccer"},
    {"name": "La Liga", "code": "esp.1", "sport": "soccer"},
    {"name": "Bundesliga", "code": "ger.1", "sport": "soccer"},
    {"name": "Serie A", "code": "ita.1", "sport": "soccer"},
    {"name": "Ligue 1", "code": "fra.1", "sport": "soccer"},
    {"name": "Süper Lig", "code": "tur.1", "sport": "soccer"},
    {"name": "Champions League", "code": "uefa.champions", "sport": "soccer"},
    {"name": "Europa League", "code": "uefa.europa", "sport": "soccer"},
    {"name": "Conference Lg", "code": "uefa.europa.conf", "sport": "soccer"},
    {"name": "NBA", "code": "nba", "sport": "basketball"},
    {"name": "EuroLeague", "code": "basketball.euroleague", "sport": "basketball"}
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

today = datetime.now()
dates_to_fetch = []
for i in range(5): 
    target = today + timedelta(days=i)
    dates_to_fetch.append(target.strftime("%Y%m%d"))

print(f"DEBUG: Fetching for dates: {dates_to_fetch}")

total_found = 0
for league in LEAGUES:
    for date_str in dates_to_fetch:
        url = f"http://site.api.espn.com/apis/site/v2/sports/{league['sport']}/{league['code']}/scoreboard?dates={date_str}"
        try:
            res = requests.get(url, headers=headers, timeout=5)
            data = res.json()
            events = data.get('events', [])
            count = len(events)
            total_found += count
            if count > 0:
                print(f"FOUND {count} in {league['name']}")
                # DEBUG ODDS STRUCTURE
                try:
                    ev = events[0]
                    odds = ev.get('competitions', [{}])[0].get('odds', [])
                    if odds:
                        import json
                        print("SAMPLE ODDS DATA:")
                        print(json.dumps(odds[0], indent=2))
                except: pass
        except Exception as e:
            print(f"ERROR {league['name']} {date_str}: {e}")

print(f"DEBUG: Total matches found: {total_found}")
