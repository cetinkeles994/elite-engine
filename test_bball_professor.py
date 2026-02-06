
from scraper_engine import fetch_matches_for_dates
from datetime import datetime

# Test leagues
leagues = [
    {"name": "NBA", "code": "nba", "sport": "basketball"},
    {"name": "EuroLeague", "code": "eur.league", "sport": "basketball", "sofascore_id": 42527}
]

test_date = "20260206"
dates = [test_date]

print(f"--- DEBUG: Testing PROFESSOR LEVEL Predictions for {test_date} ---")
matches = fetch_matches_for_dates(dates, leagues)

print(f"--- RESULT ---")
for m in matches:
    stats = m['pro_stats']
    sim = stats.get('sim_details', {})
    print(f"League: {m['league']:12} | Match: {m['home']:25} vs {m['away']:25}")
    print(f"  > Pred: {stats['total_points']} | Pick: {stats['best_goal_pick']}")
    print(f"  > Props: {stats.get('best_props_pick')} (Prob: {stats.get('best_props_prob')}%)")
    print(f"  > Sim: Home %{int(sim.get('home_win_prob',0))} - Away %{int(sim.get('away_win_prob',0))} | Over %{int(sim.get('over_2_5_prob',0))}")
    print("-" * 50)
