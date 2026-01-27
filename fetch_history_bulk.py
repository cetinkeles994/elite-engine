from scraper_engine import fetch_matches_for_dates, save_training_data
from datetime import datetime, timedelta

def run():
    print("📜 Starting Bulk History Fetch for AI Training...")
    
    LEAGUES = [
        {"name": "Premier League", "code": "eng.1", "sport": "soccer"},
        {"name": "La Liga", "code": "esp.1", "sport": "soccer"},
        {"name": "Bundesliga", "code": "ger.1", "sport": "soccer"},
        {"name": "Serie A", "code": "ita.1", "sport": "soccer"},
        {"name": "Ligue 1", "code": "fra.1", "sport": "soccer"},
        {"name": "Süper Lig", "code": "tur.1", "sport": "soccer"},
        {"name": "Champions League", "code": "uefa.champions", "sport": "soccer"},
        {"name": "Europa League", "code": "uefa.europa", "sport": "soccer"},
        {"name": "NBA", "code": "nba", "sport": "basketball"},
        {"name": "EuroLeague", "code": "basketball.euroleague", "sport": "basketball"}
    ]
    
    today = datetime.now()
    dates_to_fetch = []
    
    # Fetch last 30 days
    DAYS_BACK = 30
    print(f"📅 Generating dates for the last {DAYS_BACK} days...")
    
    for i in range(1, DAYS_BACK + 1):
        target = today - timedelta(days=i)
        dates_to_fetch.append(target.strftime("%Y%m%d"))
        
    print(f"🔄 Fetching data from ESPN API (This might take a minute)...")
    matches = fetch_matches_for_dates(dates_to_fetch, LEAGUES)
    
    print(f"✅ Found {len(matches)} historical matches.")
    
    print("💾 Saving to training_data.csv...")
    save_training_data(matches)
    
    print("🚀 Bulk Data Collection Complete!")

if __name__ == "__main__":
    run()
