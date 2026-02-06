
import requests

leagues = ["nba", "evrl", "euroleague", "mens-euroleague", "euro-league", "intl.1"]
date = "20260206"

for l in leagues:
    url = f"http://site.api.espn.com/apis/site/v2/sports/basketball/{l}/scoreboard?dates={date}"
    res = requests.get(url)
    if res.status_code == 200:
        data = res.json()
        events = data.get('events', [])
        print(f"League: {l} | Events: {len(events)}")
    else:
        print(f"League: {l} | Status: {res.status_code}")
