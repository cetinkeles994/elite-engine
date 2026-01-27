
from scraper_engine import SofaScoreAdapter, StatEngine
import json

def test_integration():
    adapter = SofaScoreAdapter("sofascore_data.json")
    print(f"Loaded {len(adapter.data_map)} matches from SofaScore cache.")
    
    # Test mapping
    match_id = adapter.get_event_id("St. Pauli", "RB Leipzig")
    print(f"Mapping 'St. Pauli vs RB Leipzig' -> ID: {match_id}")
    
    stats = adapter.get_deep_stats("St. Pauli", "RB Leipzig")
    print(f"Deep Stats for St. Pauli vs Leipzig: {stats}")
    
    # Test Global Odds Flow (Baron Signals 2.0)
    print("\n--- TESTING BARON SIGNALS 2.0 (GLOBAL FLOW) ---")
    mock_bookie_odds = 2.10
    # sofa_data already contains global_odds: {'1': 4.33, ...} from the cache
    # Let's override for the test
    stats['global_odds'] = {'1': 1.85, 'X': 3.40, '2': 4.50}
    
    engine = StatEngine()
    preds = engine.predict_match(0.40, 0.40, "ger.1", sofa_data=stats)
    
    if preds.get('global_market'):
        print(f"✅ SUCCESS: Global Market Data detected in prediction: {preds['global_market']}")
        g_home = preds['global_market'].get('1')
        if mock_bookie_odds > g_home * 1.05:
            print(f"✅ SUCCESS: Global Lag of {round(((mock_bookie_odds - g_home)/mock_bookie_odds)*100, 1)}% theoretically detectable!")
    else:
        print("❌ FAILURE: Global market data not found in prediction.")

if __name__ == "__main__":
    test_integration()
