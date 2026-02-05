import requests
import json
import time

def test_sofascore():
    # Attempting to fetch with more realistic browser headers
    date_str = "2026-02-01"
    url = f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{date_str}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.sofascore.com/",
        "Origin": "https://www.sofascore.com",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Cache-Control": "no-cache"
    }
    
    print(f"Testing SofaScore API for {date_str}...")
    try:
        session = requests.Session()
        # Sometimes a warmup request to the home page helps
        # session.get("https://www.sofascore.com", headers=headers, timeout=5)
        
        res = session.get(url, headers=headers, timeout=10)
        print(f"Status Code: {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            events = data.get('events', [])
            print(f"Success! Found {len(events)} events.")
            
            # Search for Turkish matches
            turkish = [e for e in events if e.get('tournament', {}).get('category', {}).get('name') == 'Turkey']
            print(f"Turkish matches found: {len(turkish)}")
            for e in turkish:
                print(f"- {e['name']} (Tournament: {e['tournament']['name']} ID: {e['tournament']['id']})")
        else:
            print(f"Failed. Response: {res.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test_sofascore()
