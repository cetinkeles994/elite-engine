import cloudscraper
import json

scraper = cloudscraper.create_scraper()
headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.sofascore.com/"
}

# Example event ID for a recent match (I'll try to find one from a daily list or use a known one)
# For now, I'll fetch today's events to get a real ID
test_date = "2026-02-11"
sport = "football"
url_fixtures = f"https://api.sofascore.com/api/v1/sport/{sport}/scheduled-events/{test_date}"

try:
    print(f"Fetching fixtures for {test_date}...")
    res = scraper.get(url_fixtures, headers=headers)
    print(f"Fixtures status: {res.status_code}")
    if res.status_code == 200:
        events = res.json().get('events', [])
        print(f"Found {len(events)} events.")
        if events:
            # Try to find a match that likely has lineups (e.g. Major leagues)
            event_id = None
            for ev in events:
                if ev.get('tournament', {}).get('category', {}).get('name') in ['England', 'Spain', 'Germany']:
                    event_id = ev.get('id')
                    match_name = ev.get('name')
                    break
            
            if not event_id:
                event_id = events[0].get('id')
                match_name = events[0].get('name')

            print(f"Testing with: {match_name} (ID: {event_id})")
            
            # Now test missing-players
            url_missing = f"https://api.sofascore.com/api/v1/event/{event_id}/missing-players"
            print(f"Fetching missing players from: {url_missing}")
            res_missing = scraper.get(url_missing, headers=headers)
            print(f"Missing players status: {res_missing.status_code}")
            if res_missing.status_code == 200:
                missing_data = res_missing.json()
                print("✅ Found missing players data:")
                print(json.dumps(missing_data, indent=2, ensure_ascii=False))
            else:
                print(f"❌ Missing players endpoint returned: {res_missing.status_code}")
    else:
        print(f"Error data: {res.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
