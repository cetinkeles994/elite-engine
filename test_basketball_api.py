
import requests

leagues = [
    {"name": "NBA", "code": "nba", "sport": "basketball"},
    {"name": "EuroLeague", "code": "mens-euroleague", "sport": "basketball"},
    {"name": "EuroCup", "code": "mens-eurocup", "sport": "basketball"},
    {"name": "BSL", "code": "tur.1", "sport": "basketball"}
]

for l in leagues:
    url = f"http://site.api.espn.com/apis/site/v2/sports/{l['sport']}/{l['code']}/scoreboard"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            count = len(data.get('events', []))
            print(f"DEBUG: {l['name']} ({l['code']}) -> {count} matches found")
        else:
            print(f"DEBUG: {l['name']} ({l['code']}) -> FAILED (Status {res.status_code})")
    except Exception as e:
        print(f"DEBUG: {l['name']} ({l['code']}) -> ERROR: {e}")
