import scraper_engine
import json

def health_check():
    print("Checking normalize_name...")
    print(f"Result: {scraper_engine.normalize_name('Fenerbahçe')}")
    
    print("\nChecking fetch_standings (mocking requests)...")
    # We can't easily mock requests here without a mocking lib, 
    # but we can try a real call to a reliable league.
    try:
        data = scraper_engine.fetch_standings("eng.1")
        print(f"Standings Success: Found {len(data) if data else 0} teams")
        print(f"TEAM_ID_MAP populated? {len(scraper_engine.TEAM_ID_MAP) > 0}")
    except Exception as e:
        print(f"Standings Failure: {e}")

    print("\nChecking fetch_h2h_data (with dummy IDs)...")
    try:
        # This will likely return None or empty list but shouldn't CRASH
        res = scraper_engine.fetch_h2h_data("dummy_id", "Galatasaray", "Fenerbahce")
        print(f"H2H Success (Fallback test): {res}")
    except Exception as e:
        print(f"H2H Failure: {e}")

if __name__ == "__main__":
    health_check()
