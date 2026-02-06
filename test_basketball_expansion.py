
from scraper_engine import SUPPORTED_LEAGUES, fetch_matches_for_dates
from datetime import datetime, timedelta

def test_basketball_expansion():
    print("🏀 Testing Basketball Expansion...")
    
    # Filter only new basketball leagues
    new_leagues = [l for l in SUPPORTED_LEAGUES if l['sport'] == 'basketball' and l['name'] != 'NBA']
    
    today = datetime.now().strftime("%Y%m%d")
    dates = [today]
    
    print(f"Checking leagues: {[l['name'] for l in new_leagues]}")
    matches = fetch_matches_for_dates(dates, new_leagues)
    
    print(f"\n✅ Total New Basketball Matches Found: {len(matches)}")
    for m in matches:
        print(f"[{m['league']}] {m['home']} vs {m['away']} - Status: {m['time']}")

if __name__ == "__main__":
    test_basketball_expansion()
