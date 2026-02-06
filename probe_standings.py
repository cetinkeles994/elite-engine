
import requests
import json

leagues = ["spa.1", "acb", "tur.1", "ita.1", "ger.1"]
date = "20260206"

for l in leagues:
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/{l}/standings"
    res = requests.get(url)
    if res.status_code == 200:
        print(f"Standings SUCCESS: {l}")
    else:
        print(f"Standings FAILED: {l} ({res.status_code})")
        
    url_score = f"https://site.api.espn.com/apis/site/v2/sports/basketball/{l}/scoreboard?dates={date}"
    res = requests.get(url_score)
    if res.status_code == 200:
        print(f"Scoreboard SUCCESS: {l}")
    else:
        print(f"Scoreboard FAILED: {l} ({res.status_code})")
