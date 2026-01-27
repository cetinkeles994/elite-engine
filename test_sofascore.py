import cloudscraper
import json

def test_sofascore():
    # Use cloudscraper to bypass Cloudflare
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    # Tested minimal headers that mirrored 'read_url_content'
    headers = {
        "User-Agent": "Go-http-client/2.0",
        "Accept": "*/*",
        "X-Requested-With": "4795b7",
        "Origin": "https://www.sofascore.com",
        "Referer": "https://www.sofascore.com/",
    }
    
    # Try fetching live football events
    urls = [
        "https://api.sofascore.com/api/v1/sport/football/events/live",
        "https://www.sofascore.com/api/v1/sport/football/events/live"
    ]
    
    for url in urls:
        print(f"\nTesting SofaScore API with CloudScraper: {url}")
        try:
            # If same-site, we might need same-origin headers for www path
            if "www.sofascore.com" in url:
                headers["Sec-Fetch-Site"] = "same-origin"
            else:
                headers["Sec-Fetch-Site"] = "same-site"

            response = scraper.get(url, headers=headers, timeout=10)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                events = data.get('events', [])
                print(f"Success! Found {len(events)} live matches.")
                if events:
                    first = events[0]
                    print(f"Example Match: {first.get('homeTeam', {}).get('name')} vs {first.get('awayTeam', {}).get('name')}")
                    print(f"Event ID: {first.get('id')}")
            else:
                print(f"Failed to fetch data from {url}. Status: {response.status_code}")
                # print(f"Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"Error for {url}: {e}")

if __name__ == "__main__":
    test_sofascore()
