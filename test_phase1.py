import scraper_engine
from sofascore_adapter import SofaScoreAdapter

def test_phase1():
    print("🧪 Testing Phase 1: Real AI Integration...")
    
    # 1. Test Form Fetching
    team_name = "Galatasaray"
    print(f"\n🔍 Fetching form for {team_name}...")
    form_str, form_score = scraper_engine.fetch_team_form(team_name, "tur.1")
    print(f"📊 Result: Form={form_str}, Score={form_score}")
    
    # 2. Test Prediction with Form Impact (Soccer)
    print(f"\n⚽ Testing Soccer Prediction (Galatasaray vs Fenerbahce)...")
    # Mock some basic stats
    scraper_engine.STANDINGS_CACHE["tur.1"] = [
        {'team': 'Galatasaray', 'played': 20, 'gf': 50, 'ga': 10},
        {'team': 'Fenerbahce', 'played': 20, 'gf': 45, 'ga': 15}
    ]
    
    preds = scraper_engine.stat_engine.predict_match(
        home_win_rate=55,
        away_win_rate=45,
        league_code="tur.1",
        sport="soccer",
        home_team="Galatasaray",
        away_team="Fenerbahce"
    )
    
    print(f"📈 xG: {preds['home_goals']} - {preds['away_goals']}")
    print(f"🏷️ Badges: {preds.get('home_badge', '')} | {preds.get('away_badge', '')}")
    print(f"🔗 Data Source: {preds['data_source']}")

    # 3. Test Prediction with Form Impact (Basketball)
    print(f"\n🏀 Testing Basketball Prediction (Lakers vs Warriors)...")
    preds_bball = scraper_engine.stat_engine.predict_match(
        home_win_rate=60,
        away_win_rate=40,
        league_code="nba",
        sport="basketball",
        home_team="Lakers",
        away_team="Warriors"
    )
    
    print(f"📈 Expected Points: {preds_bball['home_points_pred']} - {preds_bball['away_points_pred']}")
    print(f"🔗 Data Source: {preds_bball['data_source']}")

if __name__ == "__main__":
    test_phase1()
