import json
import os
from datetime import datetime
from scraper_engine import scrape_todays_fixtures

def run_elite_update():
    """
    The main robot function. Scrapes all data and saves to a static cache.
    """
    print(f"--- 🚀 Elite Data Update Started: {datetime.now()} ---")
    
    try:
        # 1. Scrape all fixtures (This does the heavy lifting: ESPN + SofaScore blending)
        print("🔍 Scraping fixtures and deep stats...")
        matches = scrape_todays_fixtures()
        
        # 2. Save to Static Cache
        cache_file = "matches_cache.json"
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(matches, f, indent=4, ensure_ascii=False)
            
        print(f"✅ SUCCESS: {len(matches)} matches saved to {cache_file}")
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    run_elite_update()
