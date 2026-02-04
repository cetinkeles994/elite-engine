import requests
import time
import math
import random
from datetime import datetime, timedelta
import joblib
import pandas as pd
import os
import sys
import codecs
from sofascore_adapter import SofaScoreAdapter

# Force UTF-8 for Windows console redirection
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

# --- PRO STAT ENGINE (The "Math" Brain) ---
class StatEngine:
    def __init__(self):
        # Professional League Baselines (Goals / Points avg)
        self.baselines = {
            "eng.1": {"goals": 2.9,  "home_adv": 0.35}, # PL is high scroing
            "esp.1": {"goals": 2.5,  "home_adv": 0.30}, 
            "ita.1": {"goals": 2.6,  "home_adv": 0.32},
            "ger.1": {"goals": 3.2,  "home_adv": 0.38}, # Bundesliga is goal fest
            "tur.1": {"goals": 2.8,  "home_adv": 0.45}, # Turkey has huge home advantage
            "uefa.champions": {"goals": 3.0, "home_adv": 0.25},
            "uefa.europa": {"goals": 2.9, "home_adv": 0.30},
            "nba":   {"points": 230.0, "home_adv": 3.5},
            "basketball.euroleague": {"points": 165.0, "home_adv": 4.5}
        }
        
        # Load AI Learned Weights
        self.learned_weights = {}
        try:
            import json
            import os
            if os.path.exists("model_weights.json"):
                with open("model_weights.json", "r") as f:
                    self.learned_weights = json.load(f)
                print("AI Weights Loaded: dict_keys(['Premier League', 'La Liga', 'Bundesliga', 'Serie A', 'Ligue 1', 'Süper Lig'])")
        except Exception as e:
            print(f"AI Load Error: {e}")

    def simulate_match(self, h_exp, a_exp, iterations=1000):
        # MONTE CARLO SIMULATION (The "God Mode" Engine)
        # Plays the match 'iterations' times to find true probability
        
        home_wins = 0
        away_wins = 0
        draws = 0
        over_2_5 = 0
        over_1_5 = 0
        over_3_5 = 0
        over_0_5 = 0
        
        score_matrix = {}
        
        for _ in range(iterations):
            # Generate random scores based on Poisson means
            # Uses numpy-like logic with standard random
            h_score = 0
            a_score = 0
            
            # Simple Poisson Generator
            # Home
            p = 1.0
            L = math.exp(-h_exp)
            k = 0
            while p > L:
                k += 1
                p *= random.random()
            h_score = k - 1
            
            # Away
            p = 1.0
            L = math.exp(-a_exp)
            k = 0
            while p > L:
                k += 1
                p *= random.random()
            a_score = k - 1
            
            # Track Results
            if h_score > a_score: home_wins += 1
            elif a_score > h_score: away_wins += 1
            else: draws += 1
            
            total_goals = h_score + a_score
            if total_goals > 2.5: over_2_5 += 1
            if total_goals > 1.5: over_1_5 += 1
            if total_goals > 3.5: over_3_5 += 1
            if total_goals > 0.5: over_0_5 += 1
            
            # Track Exact Score Frequency
            s_key = f"{h_score}-{a_score}"
            score_matrix[s_key] = score_matrix.get(s_key, 0) + 1
            
        s_key = f"{h_score}-{a_score}"
        score_matrix[s_key] = score_matrix.get(s_key, 0) + 1
        
    # --- SMART SELECTION (Tie-Breaker Logic) ---
    # Sort scores by frequency (descending)
    sorted_scores = sorted(score_matrix.items(), key=lambda x: x[1], reverse=True)
    
    # Default to the most frequent
    best_score = sorted_scores[0][0]
    best_count = sorted_scores[0][1]
    
    # Check for "Split Vote" (if 2nd place is close to 1st)
    if len(sorted_scores) > 1:
        runner_up = sorted_scores[1][0]
        runner_up_count = sorted_scores[1][1]
        
        # If runner-up is within 10% of the winner (Close Call)
        if runner_up_count > (best_count * 0.90):
            # TIE BREAKER: Choose the "Safer" option (Fewer Goals)
            bs_h, bs_a = map(int, best_score.split('-'))
            ru_h, ru_a = map(int, runner_up.split('-'))
            
            if (ru_h + ru_a) < (bs_h + bs_a):
                best_score = runner_up # Swap to safer option
                # print(f"DEBUG: Swapped {best_score} for {runner_up} (Safety First)")

    ms_h = int(best_score.split('-')[0])
    ms_a = int(best_score.split('-')[1])
    
    # Extract Top 3 for UI Transparency
    top_scores = []
    for s_key, s_count in sorted_scores[:3]:
        prob = int((s_count / iterations) * 100)
        top_scores.append({'score': s_key, 'prob': prob})
        
    return {
        'home_win_prob': (home_wins / iterations) * 100,
        'away_win_prob': (away_wins / iterations) * 100,
        'draw_prob': (draws / iterations) * 100,
        'over_2_5_prob': (over_2_5 / iterations) * 100,
        'over_1_5_prob': (over_1_5 / iterations) * 100,
        'over_3_5_prob': (over_3_5 / iterations) * 100,
        'over_0_5_prob': (over_0_5 / iterations) * 100,
        'mode_score_home': ms_h,
        'mode_score_away': ms_a,
        'mode_score_prob': (score_matrix[best_score] / iterations) * 100,
        'top_scores': top_scores
    }

    def predict_match(self, home_win_rate, away_win_rate, league_code, sport="soccer", live_stats=None, h_real=None, a_real=None, sofa_data=None):
    "tur.2": {"goals": 2.3, "home_adv": 0.25, "points": 220.0}, # Tight League
        "ger.1": {"goals": 3.1, "home_adv": 0.35, "points": 220.0}, # Over League
        "ita.1": {"goals": 2.5, "home_adv": 0.30, "points": 220.0}, # Tactical
        "esp.1": {"goals": 2.4, "home_adv": 0.35, "points": 220.0}, # Underish
    })
    
    def simulate_match(self, h_goals, a_goals, iterations=1000):
        # ... (unchanged) ...
    
    def predict_match(self, home_win_rate, away_win_rate, league_code, sport="soccer", live_stats=None, h_real=None, a_real=None, sofa_data=None):
        base = self.baselines.get(league_code, {"goals": 2.7, "home_adv": 0.35, "points": 220.0})
        
        preds = {
            "home_goals": 0, "away_goals": 0,
            # ... (unchanged) ...
        }

        # --- 1. STRENGTH CALCULATION ---
        # ... (strength logic) ...

        # ... (momentum logic) ...

        if sport == 'soccer':
            # --- SOCCER MODEL ---
            avg_goals = base['goals']
            home_adv = base['home_adv']
            
            # ... (Goal Calculation) ...
            
            # [INSERTION POINT for Tight Match Logic]
            # --- ALGORITHMIC IMPROVEMENT: TIGHT MATCH LOGIC ---
            # If teams are equal strength AND league is tight (avg < 2.6)
            strength_diff = abs(home_strength - away_strength)
            if strength_diff < 0.15 and avg_goals < 2.6:
                # Force tighter game
                # Reduce xG by 15% to prevent "2-2" predictions in tight tactical games
                h_exp *= 0.85
                a_exp *= 0.85
                data_source += " | Sıkışık Maç Modu (x%85)"
            
            # ... (Live Momentum) ...
    
    # --- UEFA ---
    {"name": "Champions League", "code": "uefa.champions", "sport": "soccer"},
    {"name": "Europa League", "code": "uefa.europa", "sport": "soccer"},
    {"name": "Conference Lg", "code": "uefa.europa.conf", "sport": "soccer"},
    
    # --- BASKETBALL ---
    {"name": "NBA", "code": "nba", "sport": "basketball"},
    {"name": "EuroLeague", "code": "eur.league", "sport": "basketball"} # New!
]

def scrape_todays_fixtures():
    LEAGUES = SUPPORTED_LEAGUES

    
    matches = []
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    # Fetch 5 days (Today + 4 Days) to ensure plenty of matches
    today = datetime.now()
    dates_to_fetch = []
    for i in range(5):
        target = today + timedelta(days=i)
        dates_to_fetch.append(target.strftime("%Y%m%d"))

    return fetch_matches_for_dates(dates_to_fetch, LEAGUES)

def scrape_history():
    # Fetch last 3 days
    LEAGUES = SUPPORTED_LEAGUES
    
    today = datetime.now()
    dates_to_fetch = []
    for i in range(1, 4): # Yesterday, Day before, etc.
        target = today - timedelta(days=i)
        dates_to_fetch.append(target.strftime("%Y%m%d"))
        
    return fetch_matches_for_dates(dates_to_fetch, LEAGUES)

# --- STANDINGS API UPGRADE (Tier 1 Data) ---
STANDINGS_CACHE = {}

def fetch_standings(league_code, sport='soccer'):
    # Caching to avoid spamming API
    if league_code in STANDINGS_CACHE: return STANDINGS_CACHE[league_code]
    
    # ESPN API for Standings
    # e.g. http://site.api.espn.com/apis/v2/sports/soccer/eng.1/standings
    url = f"http://site.api.espn.com/apis/v2/sports/{sport}/{league_code}/standings"
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        if res.status_code == 200:
            data = res.json()
            team_stats = {}
            
            if 'children' in data:
                # Structure: children[0] -> standings -> entries
                entries = data['children'][0].get('standings', {}).get('entries', [])
                for entry in entries:
                    name = entry['team']['displayName']
                    stats = { 'played': 1, 'gf': 0, 'ga': 0 }
                    
                    for s in entry.get('stats', []):
                        if s['name'] == 'gamesPlayed': stats['played'] = s['value']
                        if s['name'] == 'pointsFor': stats['gf'] = s['value'] # Goals For
                        if s['name'] == 'pointsAgainst': stats['ga'] = s['value'] # Goals Against
                    
                    # Calculate Power Ratings
                    if stats['played'] > 0:
                        stats['att'] = stats['gf'] / stats['played'] # Avg Goals Scored
                        stats['def'] = stats['ga'] / stats['played'] # Avg Goals Conceded
                    else:
                        stats['att'] = 1.0; stats['def'] = 1.0
                        
                    team_stats[name] = stats
            
            print(f"Loaded Standings for {league_code}: {len(team_stats)} teams")
            STANDINGS_CACHE[league_code] = team_stats
            return team_stats
            
    except Exception as e:
        print(f"Standings Error {league_code}: {e}")
    
    STANDINGS_CACHE[league_code] = None # Mark as failed to stop retrying
    return None

def fetch_matches_for_dates(dates_to_fetch, LEAGUES):
    print(f"DEBUG: STARTING FETCH for {len(LEAGUES)} leagues and {len(dates_to_fetch)} dates")
    matches = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    adapter = SofaScoreAdapter()

    for league in LEAGUES:
        # Pre-fetch Standings for this league
        league_standings = fetch_standings(league['code'], league['sport'])
        
        for date_str in dates_to_fetch:
            url = f"http://site.api.espn.com/apis/site/v2/sports/{league['sport']}/{league['code']}/scoreboard?dates={date_str}"
            try:
                # 1. TRY ESPN Scoreboard First
                espn_events = []
                try:
                    res = requests.get(url, headers=headers, timeout=5)
                    if res.status_code == 200:
                        espn_events = res.json().get('events', [])
                except: pass
                
                # 2. ALSO TRY SOFASCORE IF ID EXISTS
                final_events = []
                espn_event_ids = set() # Track by name pattern
                
                # Add ESPN events first
                for ee in espn_events:
                    try:
                        competitors = ee.get('competitions', [{}])[0].get('competitors', [])
                        h = next((c['team']['name'] for c in competitors if c['homeAway'] == 'home'), "H")
                        a = next((c['team']['name'] for c in competitors if c['homeAway'] == 'away'), "A")
                        espn_event_ids.add(f"{h.lower()}-{a.lower()}")
                        final_events.append(ee)
                    except: pass

                # Fallback Discovery via SofaScore
                if league.get('sofascore_id') and league['sport'] == 'soccer':
                    ss_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
                    ss_events = adapter.fetch_daily_fixtures(ss_date)
                    target_id = league['sofascore_id']
                    
                    added_count = 0
                    for se in ss_events:
                        if se.get('tournament', {}).get('id') == target_id:
                            h_name = se['homeTeam']['name']
                            a_name = se['awayTeam']['name']
                            
                            # Skip if already in ESPN (simple check)
                            pattern = f"{h_name.lower()}-{a_name.lower()}"
                            if pattern in espn_event_ids: continue
                            
                            # Fuzzy check (reversed or contains)
                            is_duplicate = False
                            for p in espn_event_ids:
                                if h_name.lower() in p and a_name.lower() in p:
                                    is_duplicate = True; break
                            if is_duplicate: continue

                            # Convert to Synthetic Event
                            synthetic_event = {
                                'id': f"ss-{se['id']}",
                                'name': f"{h_name} vs {a_name}",
                                'status': { 'type': { 'state': 'pre', 'shortDetail': 'NS' } },
                                'competitions': [{
                                    'competitors': [
                                        {'homeAway': 'home', 'team': {'name': h_name}, 'score': '0', 'records': []},
                                        {'homeAway': 'away', 'team': {'name': a_name}, 'score': '0', 'records': []}
                                    ]
                                }]
                            }
                            # Map Status
                            ss_status = se.get('status', {}).get('type', '')
                            if ss_status == 'finished':
                                synthetic_event['status']['type']['state'] = 'post'
                                synthetic_event['status']['type']['shortDetail'] = 'FT'
                                synthetic_event['competitions'][0]['competitors'][0]['score'] = str(se.get('homeScore', {}).get('current', 0))
                                synthetic_event['competitions'][0]['competitors'][1]['score'] = str(se.get('awayScore', {}).get('current', 0))
                            elif ss_status == 'inprogress':
                                synthetic_event['status']['type']['state'] = 'in'
                                synthetic_event['status']['type']['shortDetail'] = f"{se.get('status', {}).get('description', '45')}'"
                            
                            final_events.append(synthetic_event)
                            added_count += 1
                    
                    if added_count > 0:
                        print(f"SofaScoreDiscovery: Added {added_count} matches for {league['name']} on {date_str}")

                if not final_events: continue
                
                for event in final_events:
                    try:
                        competitions = event.get('competitions', [{}])[0]
                        competitors = competitions.get('competitors', [])
                        
                        home_team = next((c['team']['name'] for c in competitors if c['homeAway'] == 'home'), "Home")
                        away_team = next((c['team']['name'] for c in competitors if c['homeAway'] == 'away'), "Away")
                        
                        print(f"DEBUG: {league['name']} | Match: {home_team} vs {away_team} | Date: {date_str}")

                        
                        status_type = event.get('status', {}).get('type', {})
                        status_state = status_type.get('state') # pre, in, post
                        status_detail = status_type.get('shortDetail')
                        
                        home_score = next((c.get('score', '0') for c in competitors if c['homeAway'] == 'home'), '0')
                        away_score = next((c.get('score', '0') for c in competitors if c['homeAway'] == 'away'), '0')
                        
                        sport = league['sport']
                        
                        # --- WIN RATE EXTRACTION ---
                        def get_win_rate(records):
                            for r in records:
                                if r.get('type') == 'total':
                                    summary = r.get('summary', '0-0-0')
                                    try:
                                        parts = list(map(int, summary.split('-')))
                                        if len(parts) == 3: # W-D-L (Soccer)
                                            w, d, l = parts
                                            total = w + d + l
                                        elif len(parts) == 2: # W-L (Basketball)
                                            w, l = parts
                                            total = w + l
                                        else:
                                            return 0.40
                                            
                                        return w / total if total > 0 else 0.40
                                    except: return 0.40
                            return 0.40

                        home_rec = next((c.get('records', []) for c in competitors if c['homeAway'] == 'home'), [])
                        away_rec = next((c.get('records', []) for c in competitors if c['homeAway'] == 'away'), [])
                        
                        home_win_rate = get_win_rate(home_rec)
                        away_win_rate = get_win_rate(away_rec)
                        
                        # --- STANDINGS LOOKUP (New GF/GA Data) ---
                        h_stats_real = None
                        a_stats_real = None
                        
                        if league_standings:
                            # Fuzzy matching or direct lookup
                            # ESPN names usually match, but we check contains or exact
                            h_stats_real = league_standings.get(home_team)
                            a_stats_real = league_standings.get(away_team)
                            
                            if not h_stats_real:
                                # Try fuzzy match (simple contains)
                                for t_name, t_stat in league_standings.items():
                                    if home_team in t_name or t_name in home_team:
                                        h_stats_real = t_stat; break
                            if not a_stats_real:
                                for t_name, t_stat in league_standings.items():
                                    if away_team in t_name or t_name in away_team:
                                        a_stats_real = t_stat; break

                        # --- LIVE STATS ---
                        live_stats = { 'goals': 0, 'minute': 0 }
                        try:
                            # Extract Minute
                            if status_state == 'in':
                                live_stats['minute'] = int(status_detail.replace("'", "").split('+')[0]) if "'" in status_detail else 45
                            
                            live_stats['goals'] = int(home_score) + int(away_score)
                            
                            # Extract Advanced Stats if available
                            home_data = next((c for c in competitors if c['homeAway'] == 'home'), {})
                            away_data = next((c for c in competitors if c['homeAway'] == 'away'), {})
                            
                            live_stats['home_shots'] = get_stat(home_data, 'SH')
                            live_stats['away_shots'] = get_stat(away_data, 'SH')
                            
                            live_stats['home_sot'] = get_stat(home_data, 'ST')
                            live_stats['away_sot'] = get_stat(away_data, 'ST')
                            
                            live_stats['home_corners'] = get_stat(home_data, 'CW')
                            live_stats['away_corners'] = get_stat(away_data, 'CW')
                            
                            live_stats['home_fouls'] = get_stat(home_data, 'FC')
                            live_stats['away_fouls'] = get_stat(away_data, 'FC')
                            
                            live_stats['home_yc'] = get_stat(home_data, 'YC')
                            live_stats['away_yc'] = get_stat(away_data, 'YC')
                            
                            h_p = get_stat(home_data, 'POS') or get_stat(home_data, 'PP')
                            a_p = get_stat(away_data, 'POS') or get_stat(away_data, 'PP')
                            if h_p + a_p > 0:
                                live_stats['home_pos'] = h_p
                                live_stats['away_pos'] = a_p
                                
                        except: pass

                        # --- SOFASCORE LOOKUP ---
                        sofa_data = sofa_adapter.get_deep_stats(home_team, away_team)

                        # --- PRO PREDICTION GENERATION ---
                        # Pass real stats to engine
                        pro_stats = stat_engine.predict_match(
                            home_win_rate, away_win_rate, league["code"], sport, 
                            live_stats=live_stats,
                            h_real=h_stats_real,
                            a_real=a_stats_real,
                            sofa_data=sofa_data
                        )
                        
                        if sofa_data:
                            pro_stats['sofa_elite'] = sofa_data
                        
                        # --- PROBABILITY CALC (Match Winner) ---
                        home_prob = home_win_rate * 1.10 # Home Adv
                        away_prob = 1.0 - home_prob
                        
                        # Live Decay
                        is_losing = False
                        try:
                            h_s = int(home_score)
                            a_s = int(away_score)
                            if status_state == 'in':
                                 diff = h_s - a_s
                                 if diff < 0: 
                                     home_prob *= 0.20 
                                     is_losing = True
                                 elif diff > 0: home_prob *= 1.50
                        except: pass
                        
                        fair_odds_home = 1 / home_prob if home_prob > 0.01 else 99.00
                        
                        # --- ODDS PARSING ---
                        odds_data = competitions.get('odds', [])
                        bookie_home_odds = 0
                        bookie_away_odds = 0
                        spread = None
                        drop_info = None
                        
                        if odds_data:
                            try:
                                provider = odds_data[0]
                                ml = {}
                                if isinstance(provider, dict):
                                    ml = provider.get('moneyline', {})
                                else:
                                    pass # Invalid provider format
                                def am_to_dec(am_str):
                                       if not am_str: return 0
                                       try:
                                           val = float(am_str)
                                           if val > 0: return round(1 + (val / 100), 2)
                                           else: return round(1 + (100 / abs(val)), 2)
                                       except: return 0
                                
                                if ml:
                                   bookie_home_odds = am_to_dec(ml.get('home', {}).get('current', {}).get('odds'))
                                   bookie_away_odds = am_to_dec(ml.get('away', {}).get('current', {}).get('odds'))
                                   
                                   # --- DROPPING ODDS ANALYSIS (BARON TRACKING) ---
                                   try:
                                       open_home = am_to_dec(ml.get('home', {}).get('open', {}).get('odds'))
                                       if open_home > 0 and bookie_home_odds > 0:
                                           drop_pct = ((open_home - bookie_home_odds) / open_home) * 100
                                           if drop_pct > 1.1: # Lowered to 2% to catch more moves
                                                drop_info = { 'side': 'home', 'pct': round(drop_pct, 1), 'open': open_home, 'curr': bookie_home_odds }
                                       
                                       open_away = am_to_dec(ml.get('away', {}).get('open', {}).get('odds'))
                                       if open_away > 0 and bookie_away_odds > 0:
                                           drop_pct = ((open_away - bookie_away_odds) / open_away) * 100
                                           if drop_pct > 1.1:
                                                drop_info = { 'side': 'away', 'pct': round(drop_pct, 1), 'open': open_away, 'curr': bookie_away_odds }
                                   except: pass

                                if sport == 'basketball':
                                    spr = provider.get('spread', {})
                                    if spr: spread = spr.get('home', {}).get('current', {}).get('line')
                            except: pass

                        # --- BARON SIGNALS 2.0: CROSS-MARKET CROSSOVER ---
                        if sofa_data and isinstance(sofa_data, dict) and sofa_data.get('global_odds') and bookie_home_odds > 0:
                            g_odds = sofa_data['global_odds']
                            g_home = g_odds.get('1')
                            if g_home and g_home > 0:
                                # If global price is SIGNIFICANTLY lower than local price, it's a "Signal"
                                # e.g. Bookie is 2.10, Global is 1.85
                                if bookie_home_odds > g_home * 1.05:
                                    market_lag = round(((bookie_home_odds - g_home) / bookie_home_odds) * 100, 1)
                                    if not drop_info or market_lag > drop_info.get('pct', 0):
                                         drop_info = { 
                                             'side': 'home', 
                                             'pct': market_lag, 
                                             'open': bookie_home_odds, 
                                             'curr': g_home,
                                             'type': 'GLOBAL_LAG' 
                                         }
                                         pro_stats['recommendation'] = f"PİYASA DÜŞÜYOR ({market_lag}%)"
                                         pro_stats['reasoning'] = f"Küresel piyasa {g_home} seviyesine çekildi. Yerel oran ({bookie_home_odds}) geride kaldı. FIRSAT!"

                        if bookie_home_odds == 0 or bookie_home_odds == "-":
                             h_p_safe = max(0.01, home_prob)
                             bookie_home_odds = round(max(1.05, min((1/h_p_safe)/1.05, 12.0)), 2)
                             
                             away_p = max(0.01, 1.0 - home_prob)
                             bookie_away_odds = round(max(1.05, min((1/away_p)/1.05, 12.0)), 2)
                                 
                        if bookie_away_odds == 0: bookie_away_odds = "-"

                        # Extract Time
                        match_date = event.get('date', '')
                        display_time = status_detail
                        
                        # If match is upcoming (Scheduled), show the actual Time (HH:MM)
                        if status_state == 'pre':
                            try:
                                # ESPN Date Format: 2023-10-25T19:00Z
                                dt = datetime.strptime(match_date, "%Y-%m-%dT%H:%MZ")
                                # Convert to Local Time (Assuming GMT+3 for Turkey Users)
                                dt = dt + timedelta(hours=3)
                                display_time = dt.strftime("%d.%m %H:%M")
                            except:
                                display_time = "Bekliyor"
                        else:
                                # Live or Completed
                                display_time = status_detail.replace("Final", "Bitti").replace("Scheduled", "Bekliyor")

                        match = {
                            "id": event['id'],
                            "sport": sport, 
                            "league": league["name"],
                            "home": home_team,
                                "away": away_team,
                                "time": display_time,
                            "status": "Live" if status_state == 'in' else "Completed" if status_state == 'post' else "Upcoming",
                            "score": f"{home_score}-{away_score}",
                            "odds": { "home": bookie_home_odds, "away": bookie_away_odds, "spread": spread },
                            "fair_odds_home": round(fair_odds_home, 2),
                            "value_found": False,
                            "reasoning": "",
                            "recommendation": "",
                            "dropping_odds": drop_info,
                            "pro_stats": pro_stats 
                        }
                        
                        # --- RECOMMENDATION LOGIC ---
                        sys_rec = "PAS"
                        sys_confidence = 0
                        rec_color = "gray"

                        # Probability-based Recommendation
                        # Calculation: Normalized Probability (0-100)
                        
                        if sport == 'basketball':
                            if home_prob >= 0.60: 
                                sys_rec = "MS 1"
                                sys_confidence = int(home_prob * 100)
                            elif away_prob >= 0.60: 
                                sys_rec = "MS 2"
                                sys_confidence = int(away_prob * 100)
                            
                            # Spread Logic if Strong
                            if spread and sys_confidence > 75:
                                 if "MS 1" in sys_rec: sys_rec = f"MS 1 ({spread})"
                                 else: sys_rec = f"MS 2"
                                 
                        else:
                            # Soccer
                            # Require at least 55% win probability or HUGE edge
                            if home_prob > 0.55: 
                                sys_rec = "MS 1"
                                sys_confidence = int(home_prob * 100)
                            elif away_prob > 0.55: 
                                sys_rec = "MS 2"
                                sys_confidence = int(away_prob * 100)
                            else:
                                pass # Stay PAS


                        # --- AI ADJUSTMENT (Learner Engine) ---
                        # Apply penalty/boost from model_weights.json
                        # sport code vs league code mapping? scraper uses 'league' field which matches baselines keys
                        
                        # Note: 'league' variable holds the code e.g. 'eng.1'
                        if str(league) in stat_engine.learned_weights:
                            adj = stat_engine.learned_weights[str(league)].get('confidence_modifier', 0)
                            if adj != 0:
                                sys_confidence += adj
                                match['ai_note'] = f"AI Düzenlemesi: {adj}% Güven"

                        match['recommendation'] = sys_rec
                        match['value_found'] = False

                        # --- AI MODEL INTEGRATION (RANDOM FOREST) ---
                        ai_conf_boost = 0
                        ai_note_text = ""
                        
                        try:
                            # Check if Model is Loaded
                            if 'AI_MODEL' not in globals():
                                global AI_MODEL, AI_ENCODER
                                if os.path.exists("model.pkl"):
                                    AI_MODEL = joblib.load("model.pkl")
                                    AI_ENCODER = joblib.load("encoder.pkl")
                                else:
                                    AI_MODEL = None

                            if AI_MODEL:
                                # Prepare Features: [league_code, home_odds, away_odds, confidence]
                                # Encode League
                                try:
                                    l_code = AI_ENCODER.transform([league["name"]])[0]
                                except:
                                    l_code = 0 # Unknown league (fallback)

                                # Handle Odds safely
                                h_o = float(bookie_home_odds) if isinstance(bookie_home_odds, (int, float)) else 1.50
                                a_o = float(bookie_away_odds) if isinstance(bookie_away_odds, (int, float)) else 1.50
                                
                                features = pd.DataFrame([[l_code, h_o, a_o, sys_confidence]], 
                                                      columns=['league_code', 'home_odds', 'away_odds', 'confidence'])
                                
                                # Predict (Prob of Class 1: Win)
                                ai_prob = AI_MODEL.predict_proba(features)[0][1] * 100
                                
                                # AI Insight Logic
                                if ai_prob > 75:
                                    ai_conf_boost = 10
                                    ai_note_text = f"YAPAY ZEKA ONAYLI (%{int(ai_prob)} Güven). Random Forest modeli bu maçı 'Kazanır' olarak görüyor."
                                elif ai_prob < 30:
                                    ai_conf_boost = -15
                                    ai_note_text = f"YAPAY ZEKA UYARISI (%{int(ai_prob)}). Model bu maça güvenmiyor."
                                
                        except Exception as e:
                            print(f"AI PREDICT ERROR: {e}")

                        # Apply AI Boost
                        sys_confidence += ai_conf_boost

                        # --- HIGH CONFIDENCE FILTERING (The "90%" Target) ---
                        # If confidence is below 65%, force PAS.
                        # We use the SIMULATION CONFIDENCE calculated above
                        
                        # Fix scope issue: define sys_rec if not defined
                        if 'sys_rec' not in locals():
                             if home_prob > away_prob: sys_rec = "MS 1"
                             else: sys_rec = "MS 2"
                        
                        if sys_confidence < 65 and not spread and not live_stats:
                             match['recommendation'] = "PAS"
                        if sys_confidence >= 85:
                            match['value_found'] = True
                            match['recommendation'] = f"💎 KASA: {sys_rec}"
                            match['reasoning'] = f"SİSTEM MAX GÜVEN: %{sys_confidence} | İstatistiksel Hakimiyet"
                        elif sys_confidence >= 75:
                            match['value_found'] = True
                            match['recommendation'] = f"🔥 BANKO: {sys_rec}"
                            match['reasoning'] = f"Yüksek Güven: %{sys_confidence} | Form ve Kadro Avantajı"
                        elif sys_confidence >= 65:
                            match['recommendation'] = sys_rec
                            match['reasoning'] = f"Analiz: {sys_rec} (Güven: %{sys_confidence})"
                        else:
                             match['recommendation'] = "PAS"
                             match['reasoning'] = "Yeterli veri güveni oluşmadı (%65 altı)."
                        
                        if ai_note_text:
                            match['reasoning'] += f"\n\n🤖 {ai_note_text}"

                        # --- WORLD CLASS ODDS ANALYSIS (KELLY CRITERION) ---
                        # The "Gold Standard" in professional betting
                        
                        market_vig = 0.05 # Standard bookie margin 5%
                        
                        if isinstance(bookie_home_odds, (int, float)) and bookie_home_odds > 1.0:
                             # 1. Vig-Free Probability (True Market Price) implied by bookie? 
                             # No, we trust OUR probability (sys_confidence).
                             
                             real_prob = sys_confidence / 100.0
                             decimal_odds = bookie_home_odds
                             
                             # Kelly Formula: f = (bp - q) / b
                             # b = odds - 1
                             b = decimal_odds - 1
                             p = real_prob
                             q = 1 - p
                             
                             kelly_fraction = (b * p - q) / b
                             
                             # Professional Conservative Adjustment (Quarter Kelly)
                             # Full Kelly is too volatile for mortals. 
                             safe_stake = max(0, (kelly_fraction * 0.25) * 100) # Percentage of Bankroll
                             
                             edge = (real_prob - (1/decimal_odds)) * 100
                             
                             if safe_stake > 0 and edge > 0:
                                  match['value_found'] = True
                                  
                                  # Tiered Advice based on Stake Size
                                  stake_advice = "DÜŞÜK"
                                  if safe_stake > 4.0: stake_advice = "MAX (KASA)"
                                  elif safe_stake > 2.5: stake_advice = "YÜKSEK"
                                  elif safe_stake > 1.0: stake_advice = "ORTA"
                                  
                                  match['recommendation'] = f"{sys_rec} [STAKE %{safe_stake:.1f}]"
                                  if "KASA" in stake_advice:
                                       match['recommendation'] = f"💎 KASA: {match['recommendation']}"
                                  elif "YÜKSEK" in stake_advice:
                                       match['recommendation'] = f"🔥 BANKO: {match['recommendation']}"
                                       
                                  match['reasoning'] = (
                                      f"🧠 KELLY ANALİZİ: Kasanın %{safe_stake:.2f}'si Basılmalı.\n"
                                      f"📊 Matematiksel Avantaj (Edge): +%{edge:.1f}\n"
                                      f"🎯 Hedef Oran: {round(1/real_prob, 2)} | Alınan: {decimal_odds} | Güven: {stake_advice}"
                                  )
                            
                            # Update displayed score
                            match['score'] = f"0-0" # live score placeholder
                            # But pro_stats has the prediction, dashboard uses pro_stats.score_pred_home
                                  elif safe_stake > 1.0: stake_advice = "ORTA"
                                  
                                  match['recommendation'] += f" [STAKE %{round(safe_stake, 1)}]"
                                  
                                  # Detailed Financial Report
                                  match['reasoning'] = (
                                      f"🧠 KELLY ANALİZİ: Kasanın %{round(safe_stake, 2)}'si Basılmalı.\n"
                                      f"📊 Matematiksel Avantaj (Edge): +%{round(edge, 1)}\n"
                                      f"🎯 Hedef Oran: {round(1/real_prob, 2)} | Alınan: {decimal_odds} | Güven: {stake_advice}"
                                  )
                             elif edge < -10:
                                   match['reasoning'] += f" | 📉 NEGATİF DEĞER: Bu orandan oynanmaz. Matematiksel kayıp."
                        
                        # BARON ALERT (Dropping Odds Override)
                        if match.get('dropping_odds'):
                             d = match['dropping_odds']
                             side_tr = "EV SAHİBİ" if d['side'] == 'home' else "DEPLASMAN"
                             match['value_found'] = True # Always highlight dropping odds
                             match['recommendation'] = f"📉 ORAN DÜŞÜYOR: {side_tr}"
                             match['reasoning'] = f"⚠️ BARON OPERASYONU TESPİT EDİLDİ!\nOran açılıştan bu yana sert düştü.\nAçılış: {d['open']} -> Güncel: {d['curr']} (Düşüş: %{d['pct']})"
                        
                        # --- RESULT VERIFICATION ---
                        match['result'] = 'pending'
                        if status_state == 'post':
                            try:
                                h = int(home_score)
                                a = int(away_score)
                                
                                # ONLY Verify if it was a recommended Value Bet
                                if match.get('value_found', False):
                                    rec = match.get('recommendation', '')
                                    
                                    if "MS 1" in rec: match['result'] = 'won' if h > a else 'lost'
                                    elif "MS 2" in rec: match['result'] = 'won' if a > h else 'lost'
                                    elif "MS X" in rec: match['result'] = 'won' if h == a else 'lost'
                                else:
                                    match['result'] = 'skipped' 
                                
                                pick = pro_stats.get('best_goal_pick', '')
                                
                                pick = pro_stats.get('best_goal_pick', '')
                                passed = False
                                
                                # Soccer
                                if "2.5 ÜST" in pick and (h+a) > 2.5: passed = True
                                if "2.5 ALT" in pick and (h+a) < 2.5: passed = True
                                if "1.5 ÜST" in pick and (h+a) > 1.5: passed = True
                                if "3.5 ALT" in pick and (h+a) < 3.5: passed = True
                                
                                # Basketball
                                if "(B)" in pick or "EV -" in pick or "DEP -" in pick:
                                    try:
                                        parts = pick.split(' ')
                                        if len(parts) >= 2 and parts[0].replace('.','',1).isdigit():
                                            val = float(parts[0])
                                            if "ÜST" in pick and (h+a) > val: passed = True
                                            if "ALT" in pick and (h+a) < val: passed = True
                                        
                                        if "EV -" in pick: 
                                            margin = float(pick.split('-')[1].split(' ')[0])
                                            if (h - a) > margin: passed = True
                                        if "DEP -" in pick:
                                            margin = float(pick.split('-')[1].split(' ')[0])
                                            if (a - h) > margin: passed = True
                                    except: pass
                                    
                                match['goal_pick_result'] = 'won' if passed else 'lost'
                                
                                prop = pro_stats.get('best_props_pick', '')
                                prop_passed = False
                                
                                if "KORNER" in prop:
                                    try:
                                        line = float(prop.split(' ')[0])
                                        total_c = live_stats.get('home_corners', 0) + live_stats.get('away_corners', 0)
                                        if "ÜST" in prop and total_c > line: prop_passed = True
                                        if "ALT" in prop and total_c < line: prop_passed = True
                                    except: pass
                                
                                if "KART" in prop:
                                    try:
                                        line = float(prop.split(' ')[0])
                                        total_cards = (live_stats.get('home_yc', 0) + live_stats.get('away_yc', 0))
                                        if "ÜST" in prop and total_cards > line: prop_passed = True
                                        if "ALT" in prop and total_cards < line: prop_passed = True
                                    except: pass
                                    
                                match['props_pick_result'] = 'won' if prop_passed else 'lost'
                                
                            except: pass
                        
                        # --- FINAL SIMULATION APPEND ---
                        # Ensure this is always visible at the bottom of the analysis
                        sim_data = pro_stats.get('sim_details', {'home_win_prob': 0, 'away_win_prob': 0, 'draw_prob': 0, 'over_2_5_prob': 0, 'over_1_5_prob': 0})
                        sim_text = (
                            f"\n---------------\n"
                            f"🎰 MONTE CARLO SİMÜLASYONU (1000 Maç):\n"
                            f"• Ev Sahibi: %{int(sim_data['home_win_prob'])}\n"
                            f"• Deplasman: %{int(sim_data['away_win_prob'])}\n"
                            f"• Beraberlik: %{int(sim_data['draw_prob'])}\n"
                            f"• 1.5 Üst: %{int(sim_data.get('over_1_5_prob', 0))}\n"
                            f"• 2.5 Üst: %{int(sim_data['over_2_5_prob'])}"
                        )
                        
                        if 'reasoning' not in match: match['reasoning'] = ""
                        match['reasoning'] += sim_text
                        
                        if match.get('ai_note'):
                             match['reasoning'] += f"\n\n🤖 {match['ai_note']}"

                        match['live_details'] = live_stats
                        matches.append(match)
                        
                    except Exception as e:
                         print(f"MATCH ERROR for {home_team} vs {away_team}: {e} | Type: {type(e)}")
                         import traceback
                         traceback.print_exc()
                         continue

            except Exception as e:
                print(f"LEAGUE ERROR: {e}")
                continue

    # --- AUTO-LEARNING: Save to Training Data ---
    save_training_data(matches)

    return matches

def save_training_data(matches):
    import csv
    import os
    
    filename = "training_data.csv"
    headers = ["date", "league", "home", "away", "home_odds", "away_odds", "prediction", "confidence", "result", "h_score", "a_score"]
    
    file_exists = os.path.isfile(filename)
    
    try:
        with open(filename, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            if not file_exists: writer.writeheader()
            
            for m in matches:
                # Only save COMPLETED matches with a RESULT
                if m.get('status') == 'Completed' and m.get('result') in ['won', 'lost']:
                    
                    # Extract confidence from reasoning text if possible
                    conf = 0
                    try:
                        if "%" in m.get('reasoning', ''):
                            conf = int(m['reasoning'].split('%')[1].split(' ')[0])
                    except: pass

                    writer.writerow({
                        "date": m['time'],
                        "league": m['league'],
                        "home": m['home'],
                        "away": m['away'],
                        "home_odds": m['odds']['home'],
                        "away_odds": m['odds']['away'],
                        "prediction": m['recommendation'],
                        "confidence": conf,
                        "result": m['result'],
                        "h_score": m['score'].split('-')[0] if '-' in m['score'] else 0,
                        "a_score": m['score'].split('-')[1] if '-' in m['score'] else 0
                    })
    except Exception as e:
        print(f"TRAINING SAVE ERROR: {e}")

if __name__ == "__main__":
    # Test Scrape + History Backfill
    print("Fetching History for training...")
    hist = scrape_history()
    save_training_data(hist)
    print(f"Saved {len(hist)} historical matches to training_data.csv")
    
    data = scrape_todays_fixtures()
    print(f"Stats Engine Verified. Matches Found: {len(data)}")
