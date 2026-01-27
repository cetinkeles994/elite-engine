
import requests

possibilities = [
    "basketball/euroleague",
    "basketball/eurocup",
    "basketball/turkish-bsl",
    "basketball/int",
    "basketball/mens-euroleague",
    "basketball/wnba",
    "basketball/ncaa-mens"
]

for p in possibilities:
    url = f"http://site.api.espn.com/apis/site/v2/sports/{p}/scoreboard"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            league_name = data.get('leagues', [{}])[0].get('name', 'Unknown')
            count = len(data.get('events', []))
            print(f"FOUND: {p} -> {league_name} ({count} matches)")
        else:
            print(f"FAILED: {p} (Status {res.status_code})")
    except:
        pass
