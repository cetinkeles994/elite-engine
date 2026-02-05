import cloudscraper
import json
import requests
import time

def probe():
    endpoints = [
        "https://api.sofascore.com/api/v1/sport/football/scheduled-events/2026-02-01",
        "https://www.sofascore.com/api/v1/sport/football/scheduled-events/2026-02-01"
    ]
    
    configs = [
        {
            "name": "Minimal Cloudscraper",
            "headers": {}, # Let cloudscraper handle it
            "use_cloudscraper": True
        },
        {
            "name": "Standard Browser Headers",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json",
                "Origin": "https://www.sofascore.com",
                "Referer": "https://www.sofascore.com/"
            },
            "use_cloudscraper": True
        },
        {
            "name": "Requests (No Cloudscraper)",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            },
            "use_cloudscraper": False
        }
    ]

    for end in endpoints:
        for conf in configs:
            print(f"--- Testing {conf['name']} on {end} ---")
            try:
                if conf['use_cloudscraper']:
                    scraper = cloudscraper.create_scraper()
                    res = scraper.get(end, headers=conf['headers'])
                else:
                    res = requests.get(end, headers=conf['headers'])
                
                print(f"Status: {res.status_code}")
                if res.status_code == 200:
                    data = res.json()
                    print(f"SUCCESS! Events: {len(data.get('events', []))}")
                    return # Stop on first success
            except Exception as e:
                print(f"Error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    probe()
