import cloudscraper
import json

def test_discovery():
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    date_str = "2026-02-01"
    url = f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{date_str}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Referer": "https://www.sofascore.com/",
        "X-Requested-With": "4795b7" # From the user's script
    }
    
    print(f"Testing SofaScore Discovery with CloudScraper: {url}")
    try:
        res = scraper.get(url, headers=headers, timeout=10)
        print(f"Status Code: {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            events = data.get('events', [])
            print(f"Success! Found {len(events)} events.")
            
            # Print Turkish tournaments found
            tournaments = set()
            for e in events:
                if e.get('tournament', {}).get('category', {}).get('name') == 'Turkey':
                    tournaments.add(e['tournament']['name'])
                    if any(x in e['name'] for x in ["Boluspor", "Amed", "Adana", "Demirspor"]):
                        print(f"  FOUND TARGET: {e['name']} in {e['tournament']['name']}")
            
            print(f"Turkish Tournaments found: {tournaments}")
        else:
            print(f"Failed. Status: {res.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test_discovery()
