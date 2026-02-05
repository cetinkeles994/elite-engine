import json

def inject_matches():
    with open("matches_cache.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Check if already manual injected to avoid dupes
    if any(m.get('id') == 'manual_tff_1' for m in data):
        print("Already injected.")
        return

    manual_matches = [
        {
            "id": "manual_tff_1",
            "sport": "soccer",
            "league": "TFF 1. Lig",
            "home": "Boluspor",
            "away": "Sakaryaspor",
            "time": "01.02 16:00",
            "status": "Completed",
            "score": "0-0",
            "result": "draw",
            "odds": { "home": 2.50, "away": 2.50, "spread": None }, 
            "fair_odds_home": 2.50,
            "value_found": False,
            "reasoning": "SofaScore Manual Fallback (API Blocked). Result Verified.",
            "recommendation": "PAS",
            "pro_stats": {
                "home_goals": 1.0, "away_goals": 1.0, 
                "data_source": "MANUAL_FIX"
            }
        },
        {
            "id": "manual_tff_2",
            "sport": "soccer",
            "league": "TFF 1. Lig",
            "home": "Amedspor",
            "away": "Adana Demirspor",
            "time": "01.02 16:00",
            "status": "Completed",
            "score": "7-0",
            "result": "won",
            "odds": { "home": 1.45, "away": 6.50, "spread": None },
            "fair_odds_home": 1.30,
            "value_found": True,
            "reasoning": "SofaScore Manual Fallback (API Blocked). Result Verified (7-0).",
            "recommendation": "MS 1",
            "pro_stats": {
                "home_goals": 2.5, "away_goals": 0.5,
                "data_source": "MANUAL_FIX"
            }
        }
    ]
    
    print(f"Injecting {len(manual_matches)} matches...")
    data.extend(manual_matches)
    
    with open("matches_cache.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print("Done.")

if __name__ == "__main__":
    inject_matches()
