import pandas as pd
import re

def parse_stake(prediction_str):
    """Extract stake percentage from prediction string like 'MS 2 [STAKE %11.9]'"""
    try:
        match = re.search(r'STAKE %([\d\.]+)', str(prediction_str))
        if match:
            return float(match.group(1))
    except:
        pass
    return 1.0 # Default Unit stake if not specified

def analyze():
    try:
        df = pd.read_csv("training_data.csv")
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    print(f"Total Matches in History: {len(df)}")
    
    # Filter only finished games
    finished = df[df['result'].isin(['won', 'lost'])].copy()
    print(f"Finished & Validated Bets: {len(finished)}")
    
    if len(finished) == 0:
        print("No finished bets to analyze.")
        return

    # Calculate Metrics
    finished['stake_pct'] = finished['prediction'].apply(parse_stake)
    
    # Calculate Profit/Loss per bet
    # If WON: Profit = (Odds - 1) * Stake
    # If LOST: Loss = -Stake
    
    total_bankroll_change = 0
    wins = 0
    total_bets = 0
    
    for idx, row in finished.iterrows():
        odds = 0
        if "MS 1" in str(row['prediction']): odds = float(row['home_odds'])
        elif "MS 2" in str(row['prediction']): odds = float(row['away_odds'])
        # Simplified: defaulting to match winner odds for analysis if type not clear
        # But our CSV usually logs the odds relevant to the bet? 
        # Actually checking the CSV structure:
        # home_odds, away_odds are listed.
        # The prediction column says "MS 1", "MS 2", etc.
        
        target_odds = 0
        if "MS 1" in str(row['prediction']): target_odds = row['home_odds']
        elif "MS 2" in str(row['prediction']): target_odds = row['away_odds']
        
        # If target_odds is 0 or NaN, skip
        if pd.isna(target_odds) or target_odds < 1.01: continue
        
        total_bets += 1
        stake = row['stake_pct']
        
        if row['result'] == 'won':
            wins += 1
            profit = (target_odds - 1) * stake
            total_bankroll_change += profit
        else:
            total_bankroll_change -= stake

    win_rate = (wins / total_bets) * 100 if total_bets > 0 else 0
    
    print("\n--- PERFORMANCE REPORT ---")
    print(f"✅ Total Wins: {wins}")
    print(f"❌ Total Losses: {total_bets - wins}")
    print(f"🎯 Win Rate: %{win_rate:.2f}")
    print(f"💰 Theoretical Bankroll Growth: %{total_bankroll_change:.2f}")
    
    # League Breakdown
    print("\n--- LEAGUE BREAKDOWN ---")
    league_stats = finished.groupby('league')['result'].apply(lambda x: (x == 'won').mean() * 100)
    print(league_stats.sort_values(ascending=False))

if __name__ == "__main__":
    analyze()
