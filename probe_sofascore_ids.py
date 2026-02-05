import requests
import json
import codecs
import sys

# Force UTF-8 for Windows console
if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

def probe_sofascore(date_str="2026-02-01"):
    url = f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{date_str}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            print(f"FAILED: Status {res.status_code}")
            return
        data = res.json()
        events = data.get('events', [])
        print(f"Total events on {date_str}: {len(events)}")
        
        # Track unique tournaments
        tournaments = {}
        for e in events:
            t = e.get('tournament', {})
            tid = t.get('id')
            if tid not in tournaments:
                tournaments[tid] = {
                    'name': t.get('name'),
                    'category': t.get('category', {}).get('name'),
                    'count': 1,
                    'sample': e.get('name')
                }
            else:
                tournaments[tid]['count'] += 1

        print("\n--- TURKISH TOURNAMENTS ---")
        for tid, info in tournaments.items():
            if 'Turkey' in info['category'] or 'Turkiye' in info['category']:
                print(f"ID: {tid} | Name: {info['name']} | Category: {info['category']} | Count: {info['count']} | Sample: {info['sample']}")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == '__main__':
    probe_sofascore()
