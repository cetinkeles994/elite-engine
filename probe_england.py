import requests
import json

def probe_england():
    date_str = "20260201"
    url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard?dates={date_str}"
    print(f"Probing Premier League: {url}")
    try:
        res = requests.get(url, timeout=5).json()
        events = res.get('events', [])
        print(f"Events found: {len(events)}")
        for e in events:
            print(f"  {e['name']}")
    except:
        print("Eng.1 probe failed")

if __name__ == '__main__':
    probe_england()
