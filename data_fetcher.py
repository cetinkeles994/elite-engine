import json
import os
from datetime import datetime
from scraper_engine import scrape_todays_fixtures, sofa_adapter
from telegram_bot import send_kahin_alert, format_match_alert

def run_elite_update():
    """
    The main robot function. Scrapes all data and saves to a static cache.
    """
    print(f"--- 🔮 KAHİN DATA GÜNCELLEME BAŞLADI: {datetime.now()} ---")
    
    try:
        # 0. Reset SofaScore Cache (Ensure fresh IDs for H2H)
        print("🧹 Clearing SofaScore cache for fresh data...")
        sofa_adapter.reset_cache()

        # 1. Scrape all fixtures (This does the heavy lifting: ESPN + SofaScore blending)
        print("🔍 Scraping fixtures and deep stats...")
        matches = scrape_todays_fixtures()
        
        # 2. Save to DB and Static Cache
        from db_manager import db_manager
        db_manager.save_matches_batch(matches)
        
        cache_file = "matches_cache.json"
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(matches, f, indent=4, ensure_ascii=False)
            
        print(f"✅ SUCCESS: {len(matches)} matches saved to DB and {cache_file}")

        # --- PHASE 4: TELEGRAM ALERTS ---
        print("📨 Checking for Kahin Alerts...")
        for m in matches:
            pro = m.get('pro_stats', {})
            conf = pro.get('confidence', 0)
            if conf >= 85 and m.get('sport') == 'soccer':
                msg = format_match_alert(m)
                if send_kahin_alert(msg):
                    print(f"  🔥 SENT ALERT: {m['home']} vs {m['away']} (%{conf})")

        # 3. Scrape History (Last 3 Days)
        print("📜 Scraping history data...")
        from scraper_engine import scrape_history
        history = scrape_history()
        
        # Save history to DB (if needed, or just keep in history table)
        # For now, history table in DB is for verified results. 
        # But let's save the scraped history items to the matches table as 'Finished'
        db_manager.save_matches_batch(history)
        
        history_file = "history_cache.json"
        
        # Load existing history to prevent data loss
        existing_history = []
        if os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    existing_history = json.load(f)
            except: 
                existing_history = []
        
        # Merge Logic: Update existing matches, Add new ones
        history_map = {m['id']: m for m in existing_history}
        for m in history:
            history_map[m['id']] = m # Overwrite with fresh scraped data (e.g. updated scores)
            
        combined_history = list(history_map.values())
        
        # Sort by Date (Newest First) if possible, or leave as is
        try:
            combined_history.sort(key=lambda x: x.get('time', ''), reverse=True)
        except: pass

        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(combined_history, f, indent=4, ensure_ascii=False)
            
        print(f"✅ HISTORY SUCCESS: {len(combined_history)} total matches saved to {history_file} (Merged)")
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    run_elite_update()
