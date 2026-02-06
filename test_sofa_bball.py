
import requests
import json

date = "2026-02-06"
sport = "basketball"
url = "https://www.sofascore.com/api/v1/sport/basketball/events/live"

session = requests.Session()
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

print("Visiting homepage...")
session.get("https://www.sofascore.com", headers=headers)

headers["Accept"] = "*/*"
headers["Origin"] = "https://www.sofascore.com"
headers["Referer"] = "https://www.sofascore.com/"
headers["Sec-Fetch-Site"] = "same-site"

try:
    print(f"Fetching {url}...")
    res = session.get(url, headers=headers)
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        events = data.get('events', [])
        print(f"Success! Found {len(events)} events.")
        # Print first few matches
        for e in events[:5]:
            print(f"[{e.get('tournament', {}).get('name')}] {e.get('homeTeam', {}).get('name')} vs {e.get('awayTeam', {}).get('name')}")
    else:
        print(res.text[:500])
except Exception as e:
    print(f"Error: {e}")
