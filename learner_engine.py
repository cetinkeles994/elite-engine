import csv
import json
import os

TIMESTAMP_FILE = "last_learned_at.txt"
DATA_FILE = "training_data.csv"
WEIGHTS_FILE = "model_weights.json"

def run_learner():
    print("🧠 AI LEARNER ENGINE STARTED...")
    
    if not os.path.exists(DATA_FILE):
        print("No training data found. Collect more matches first.")
        return

    # 1. Load Data
    matches = []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            matches.append(row)
    
    print(f"Loaded {len(matches)} matches for analysis.")
    
    # 2. Analyze Performance by League
    league_performance = {}
    
    for m in matches:
        league = m['league']
        result = m['result']
        pred = m['prediction']
        
        if league not in league_performance:
            league_performance[league] = {'wins': 0, 'total': 0, 'losses': 0}
            
        # Only analyze System Picks (Banko/Kasa or normal picks)
        if "PAS" not in pred and "VERİ YOK" not in pred:
            league_performance[league]['total'] += 1
            if result == 'won':
                league_performance[league]['wins'] += 1
            else:
                league_performance[league]['losses'] += 1

    # 3. Generate Weights
    weights = {}
    print("\n--- PERFORMANCE REPORT ---")
    for league, stats in league_performance.items():
        if stats['total'] < 3: continue # Need sample size
        
        win_rate = (stats['wins'] / stats['total']) * 100
        print(f"[{league}] Win Rate: {int(win_rate)}% ({stats['wins']}/{stats['total']})")
        
        # LOGIC: 
        # If Win Rate < 40%: PENALIZE (Reduce confidence by 20)
        # If Win Rate > 80%: BOOST (Increase confidence by 10)
        
        penalty = 0
        if win_rate < 30: penalty = -30
        elif win_rate < 45: penalty = -15
        elif win_rate > 80: penalty = 10
        
        if penalty != 0:
            weights[league] = { "confidence_modifier": penalty }
            print(f"   -> ADJUSTMENT: {penalty}% Confidence")

    # 4. Save Logic
    with open(WEIGHTS_FILE, 'w') as f:
        json.dump(weights, f, indent=4)
        
    print(f"\n✅ Optimization Complete. Weights saved to {WEIGHTS_FILE}")

if __name__ == "__main__":
    run_learner()
