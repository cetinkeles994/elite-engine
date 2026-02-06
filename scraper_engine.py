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

def normalize_name(name):
    if not name: return ""
    name = name.lower()
    replacements = {
        'ı': 'i', 'ü': 'u', 'ö': 'o', 'ş': 's', 'ç': 'c', 'ğ': 'g',
        'İ': 'i', 'Ü': 'u', 'Ö': 'o', 'Ş': 's', 'Ç': 'c', 'Ğ': 'g'
    }
    for k, v in replacements.items():
        name = name.replace(k, v)
    return name.strip()


class StatEngine:
    def __init__(self):
        # Professional League Baselines (Goals / Points avg)
        self.baselines = {
            "eng.1": {"goals": 2.9, "home_adv": 0.35},  # PL is high scroing
            "esp.1": {"goals": 2.5, "home_adv": 0.30},
            "ita.1": {"goals": 2.6, "home_adv": 0.32},
            # Bundesliga is goal fest
            "ger.1": {"goals": 3.2, "home_adv": 0.38},
            # Turkey has huge home advantage
            "tur.1": {"goals": 2.8, "home_adv": 0.45},
            "uefa.champions": {"goals": 3.0, "home_adv": 0.25},
            "uefa.europa": {"goals": 2.9, "home_adv": 0.30},
            "nba": {"points": 230.0, "home_adv": 3.5},
            "eur.league": {"points": 165.0, "home_adv": 4.5},
            "eur.cup": {"points": 162.0, "home_adv": 4.0},
            "tur.1_basketball": {"points": 160.0, "home_adv": 5.0},
            "spa.1_basketball": {"points": 163.0, "home_adv": 3.5},
            "ita.1_basketball": {"points": 160.0, "home_adv": 4.0},
            "fra.1_basketball": {"points": 158.0, "home_adv": 4.5},
            "ger.1_basketball": {"points": 168.0, "home_adv": 3.0}
        }

        # Load AI Learned Weights
        self.learned_weights = {}
        try:
            import json
            import os
            if os.path.exists("model_weights.json"):
                with open("model_weights.json", "r") as f:
                    self.learned_weights = json.load(f)
                print(
                    "AI Weights Loaded: dict_keys(['Premier League', 'La Liga', 'Bundesliga', 'Serie A', 'Ligue 1', 'Süper Lig'])")
        except Exception as e:
            print(f"AI Load Error: {e}")

    def _get_team_ratings(self, league_code, team_name):
        """
        Ordinaryüs Seviye: Dinamik Hücum ve Savunma Reytingi Hesaplama.
        """
        try:
            standings = STANDINGS_CACHE.get(league_code)
            if not standings or len(standings) < 4: return 1.0, 1.0
            
            norm_name = normalize_name(team_name)
            team_stats = next((s for s in standings if normalize_name(s['team']) == norm_name or norm_name in normalize_name(s['team'])), None)
            
            if not team_stats or team_stats.get('played', 0) < 3: return 1.0, 1.0
            
            total_played = sum(s.get('played', 0) for s in standings)
            if total_played == 0: return 1.0, 1.0
            
            avg_gf = sum(s.get('gf', 0) for s in standings) / total_played
            avg_ga = sum(s.get('ga', 0) for s in standings) / total_played
            
            if avg_gf == 0: avg_gf = 1
            if avg_ga == 0: avg_ga = 1
            
            t_gf_pg = team_stats['gf'] / team_stats['played']
            t_ga_pg = team_stats['ga'] / team_stats['played']
            
            off_rating = t_gf_pg / avg_gf
            def_rating = t_ga_pg / avg_ga
            
            # Clamp ratings to avoid extreme outliers
            off_rating = max(0.6, min(1.6, off_rating))
            def_rating = max(0.6, min(1.6, def_rating))
            
            return off_rating, def_rating
        except:
            return 1.0, 1.0

    def simulate_match(self, h_exp, a_exp, iterations=10000):
        # MONTE CARLO SIMULATION (The "God Mode" Engine)
        # Plays the match 'iterations' times to find true probability

        home_wins = 0
        away_wins = 0
        draws = 0
        over_2_5 = 0
        over_1_5 = 0
        over_3_5 = 0
        over_0_5 = 0
        btts_yes = 0
        btts_no = 0

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

            # BTTS Tracking
            if h_score > 0 and a_score > 0: btts_yes += 1
            else: btts_no += 1
            
            # Total Goals
            total_goals = h_score + a_score
            if total_goals > 2.5: over_2_5 += 1
            if total_goals > 1.5: over_1_5 += 1
            if total_goals > 3.5: over_3_5 += 1
            if total_goals > 0.5: over_0_5 += 1

            # Track Exact Score Frequency
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
                bs_h, bs_a = map(int, best_score.split('-'))
                ru_h, ru_a = map(int, runner_up.split('-'))
                
                # --- CONTEXT-AWARE TIE-BREAKER ---
                is_home_fav = (h_exp > a_exp + 0.4)
                is_away_fav = (a_exp > h_exp + 0.4)
                
                # 1. If Favorite, prioritize the WINNING score over a draw/loss
                if is_home_fav and (ru_h > ru_a) and (bs_h <= bs_a):
                    best_score = runner_up # Swap to Home Win (e.g. 1-1 -> 2-1)
                elif is_away_fav and (ru_a > ru_h) and (bs_a <= bs_h):
                    best_score = runner_up # Swap to Away Win
                
                # 2. If Balanced, use "Safer Option" (Fewer Goals)
                elif (not is_home_fav) and (not is_away_fav):
                    if (ru_h + ru_a) < (bs_h + bs_a):
                        best_score = runner_up # Swap to safer option
        
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
            'btts_prob': (btts_yes / iterations) * 100,
            'over_2_5_prob': (over_2_5 / iterations) * 100,
            'over_1_5_prob': (over_1_5 / iterations) * 100,
            'over_3_5_prob': (over_3_5 / iterations) * 100,
            'over_0_5_prob': (over_0_5 / iterations) * 100,
            'mode_score_home': ms_h,
            'mode_score_away': ms_a,
            'mode_score_prob': (score_matrix[best_score] / iterations) * 100,
            'top_scores': top_scores
        }

    def simulate_basketball_match(self, h_exp, a_exp, sport='basketball', iterations=10000):
        """
        Profesör Seviye: Normal Dağılım (Gaussian) tabanlı Basketbol Simülasyonu.
        """
        home_wins = 0
        away_wins = 0
        total_points_list = []
        
        # Standard Deviation for basketball (Approx 10-12 points)
        # Use a reasonable default, adjust if name indicates NBA
        sigma = 11.5 
        
        for _ in range(iterations):
            # Generate random scores based on normal distribution
            h_score = int(random.gauss(h_exp, sigma))
            a_score = int(random.gauss(a_exp, sigma))
            
            # Floor scores to 0
            h_score = max(0, h_score)
            a_score = max(0, a_score)
            
            if h_score > a_score: home_wins += 1
            else: away_wins += 1
            
            total_points_list.append(h_score + a_score)
            
        avg_total = sum(total_points_list) / iterations

        # Probabilities for various thresholds
        thresholds = [150, 160, 170, 180, 190, 200]
        probs = {}
        for t in thresholds:
            probs[f'over_{t}'] = len([p for p in total_points_list if p > t + 0.5]) / iterations * 100

        return {
            'home_win_prob': (home_wins / iterations) * 100,
            'away_win_prob': (away_wins / iterations) * 100,
            'draw_prob': 0,
            'avg_total': avg_total,
            'thresholds': probs,
            # For UI compatibility with soccer tooltips
            'over_1_5_prob': probs.get('over_160', 50),
            'over_2_5_prob': probs.get('over_170', 40),
            'btts_prob': probs.get('over_150', 60),
            'mode_score_home': int(h_exp),
            'mode_score_away': int(a_exp)
        }


    def predict_match(
    self,
    home_win_rate,
    away_win_rate,
    league_code,
    sport="soccer",
    home_team=None,
    away_team=None,
    live_stats=None,
    h_real=None,
    a_real=None,
     sofa_data=None):
        code_key = league_code
        # Map ESPN slugs back to baseline keys
        code_map = {
            "mens-euroleague": "eur.league",
            "mens-eurocup": "eur.cup",
            "mens-turkish-super-league": "tur.1_basketball",
            "mens-spanish-liga-acb": "spa.1_basketball",
            "mens-italian-lega-basket-serie-a": "ita.1_basketball",
            "mens-french-lnb-pro-a": "fra.1_basketball",
            "mens-german-bbl": "ger.1_basketball"
        }
        code_key = code_map.get(league_code, league_code)
        
        if sport == 'basketball' and code_key == league_code and league_code != 'nba':
             code_key = f"{league_code}_basketball"

        # Smarter defaults: Basketball should not default to 220 points if it's European
        default_base = {"goals": 2.7, "home_adv": 0.35, "points": 220.0}
        if sport == 'basketball':
            default_base["points"] = 165.0 # Sensible EU average
            
        base = self.baselines.get(code_key, default_base)

        # --- ORDINARYUS: OFFENSIVE/DEFENSIVE RATINGS ---
        h_off, h_def = 1.0, 1.0
        a_off, a_def = 1.0, 1.0
        
        if home_team and away_team:
            h_off, h_def = self._get_team_ratings(league_code, home_team)
            a_off, a_def = self._get_team_ratings(league_code, away_team)
            
        # Adjust baselines based on ratings
        # Formula: Expected = Baseline * Team_Offense * Opponent_Defense
        if sport == 'soccer':
            h_exp = base.get('goals', 2.7) * h_off * a_def
            a_exp = base.get('goals', 2.7) * a_off * h_def
            h_exp += base.get('home_adv', 0.35)
        else:
            # Basketball
            avg_points = base.get('points', 165.0)
            h_adv = base.get('home_adv', 4.0)
            
            # 1. Rating Based Spread (Style)
            h_style = (h_off - 1.0) * 8.0 # Offset from avg
            a_style = (a_off - 1.0) * 8.0
            
            # 2. Win Rate Based Spread (Strength)
            # Ensure win_rate is 0-1. If > 1, it's 0-100 scale.
            h_wr = home_win_rate if home_win_rate <= 1.0 else home_win_rate / 100.0
            a_wr = away_win_rate if away_win_rate <= 1.0 else away_win_rate / 100.0
            
            wr_spread = (h_wr - a_wr) * 30.0 # Approx 10% diff = 3 points
            
            h_exp = (avg_points / 2) + (h_adv / 2) + (wr_spread / 2) + (h_style / 2)
            a_exp = (avg_points / 2) - (h_adv / 2) - (wr_spread / 2) + (a_style / 2)

        preds = {
            "home_goals": 0, "away_goals": 0,
            "total_goals_prediction": 0,
            "over_2_5_prob": 0,
            "cards_prediction": 0,
            "corners_prediction": 0,
            "total_points": 0,
            "home_points_pred": 0,
            "away_points_pred": 0,
            "home_win_rate": home_win_rate,
            "away_win_rate": away_win_rate,
            "best_goal_pick": "",
            "best_goal_prob": 0,
            "score_pred_home": 0,
            "score_pred_away": 0
        }

        # --- 1. STRENGTH CALCULATION ---
        home_strength = (home_win_rate / 100.0) + 0.1  # Base strength
        away_strength = (away_win_rate / 100.0)

        # --- 2. MOMENTUM ---
        h_momentum = 1.0; a_momentum = 1.0
        if live_stats:
            h_momentum = live_stats.get('home_momentum', 1.0)
            a_momentum = live_stats.get('away_momentum', 1.0)

        # Apply Momentum
        home_strength *= h_momentum
        away_strength *= a_momentum

        data_source = "SofaScore + Elite Eng v2"

        if sport == 'soccer':
            # --- SOCCER MODEL ---
            avg_goals = base['goals']
            home_adv = base['home_adv']

            # Expected Goals (Poisson Means)
            h_exp = (avg_goals / 2) + home_adv + \
                     (home_strength - away_strength)
            a_exp = (avg_goals / 2) - (home_strength - away_strength)

            # Clamp values
            h_exp = max(0.1, h_exp)
            a_exp = max(0.1, a_exp)

            # [INSERTION POINT for Tight Match Logic]
            # --- ALGORITHMIC IMPROVEMENT: TIGHT MATCH LOGIC (TUNED v2) ---
            # If teams are equal strength AND league is tight (avg < 2.4)
            strength_diff = abs(home_strength - away_strength)
            if strength_diff < 0.15 and avg_goals < 2.4:
                # Force tighter game (Relaxed to 5% reduction)
                h_exp *= 0.95
                a_exp *= 0.95
                data_source += " | Sıkışık Maç Modu (x%95)"
            
            # --- VARIANCE INJECTION ---
            # Add micro-randomness to prevent identical outputs for identical stats
            h_exp += random.uniform(-0.05, 0.05)
            a_exp += random.uniform(-0.05, 0.05)

            # --- FAVORITE BOOST ---
            # If a team is a clear favorite (>50%), give them a slight attack boost
            if home_win_rate > 50: h_exp *= 1.05
            if away_win_rate > 50: a_exp *= 1.05

            # --- FAVORITE BOOST (UPDATED) ---
            # Now using Blended Rates (History + Market)
            # If a team is a dominant favorite (>60%), FORCE consistent xG gap
            if home_win_rate > 0.60:
                h_exp = max(h_exp, a_exp + 0.6) # Ensure at least 0.6 goal gap
                h_exp *= 1.10 # Boost further
            if away_win_rate > 0.60:
                a_exp = max(a_exp, h_exp + 0.6)
                a_exp *= 1.10

            preds['home_goals'] = round(h_exp, 2)
            preds['away_goals'] = round(a_exp, 2)
            preds['total_goals_prediction'] = round(h_exp + a_exp, 2)

            # --- GOD MODE: RUN 10000 SIMULATIONS ---
            sim_results = self.simulate_match(h_exp, a_exp, iterations=10000)

            # Use Simulated Probability
            home_prob = sim_results['home_win_prob'] / 100.0
            away_prob = sim_results['away_win_prob'] / 100.0
            preds['over_2_5_prob'] = int(sim_results['over_2_5_prob'])

            # EXACT SCORE PREDICTION
            preds['score_pred_home'] = sim_results['mode_score_home']
            preds['score_pred_away'] = sim_results['mode_score_away']

            # Pack details
            preds['sim_details'] = sim_results

            # Best Goal Pick (Enhanced with BTTS)
            probs = sim_results
            picks = []

            # 1. Over/Under Candidates
            if probs['over_2_5_prob'] > 65: picks.append(("2.5 ÜST", int(probs['over_2_5_prob'])))
            if probs['over_3_5_prob'] > 55: picks.append(("3.5 ÜST", int(probs['over_3_5_prob'])))
            if probs['over_1_5_prob'] > 80: picks.append(("1.5 ÜST", int(probs['over_1_5_prob'])))

            # Under Candidates
            if probs['over_2_5_prob'] < 35:
                if probs['over_1_5_prob'] < 45: picks.append(("1.5 ALT", int(100 - probs['over_1_5_prob'])))
                else: picks.append(("2.5 ALT", int(100 - probs['over_2_5_prob'])))

            # 2. BTTS Candidates
            if probs['btts_prob'] > 60: picks.append(
                ("KG VAR", int(probs['btts_prob'])))
            elif probs['btts_prob'] < 40: picks.append(("KG YOK", int(100 - probs['btts_prob'])))

            # Sort by Probability (Highest Confidence First)
            if picks:
                picks.sort(key=lambda x: x[1], reverse=True)
                preds['best_goal_pick'] = picks[0][0]
                preds['best_goal_prob'] = picks[0][1]
            else:
                preds['best_goal_pick'] = "GOL ANALİZ"
                preds['best_goal_prob'] = 50

            # Synergy Check (Disabled for indentation fix)
            # if "KG VAR" in preds['best_goal_pick'] and (preds['score_pred_home'] == 0 or preds['score_pred_away'] == 0):
            #     if preds['score_pred_home'] == 0: preds['score_pred_home'] = 1
            #     if preds['score_pred_away'] == 0: preds['score_pred_away'] = 1
            # elif "KG YOK" in preds['best_goal_pick'] and (preds['score_pred_home'] > 0 and preds['score_pred_away'] > 0):
            #     if preds['home_win_rate'] > preds['away_win_rate']: preds['score_pred_away'] = 0
            #     else: preds['score_pred_home'] = 0

        elif sport == 'basketball':
            # --- BASKETBALL OUTPUT PACKING ---
            preds['home_points_pred'] = int(h_exp)
            preds['away_points_pred'] = int(a_exp)
            preds['total_points'] = int(h_exp + a_exp)
            
            # Basketball Pick Logic
            # Total Points Analysis
            tp = preds['total_points']
            if tp > avg_points + 5: preds['best_goal_pick'] = f"{tp-3} ÜST"
            elif tp < avg_points - 5: preds['best_goal_pick'] = f"{tp+3} ALT"
            else: preds['best_goal_pick'] = f"{tp} ÜST"
            
            # Spread factor for prob
            spread_f = abs(h_exp - a_exp)
            preds['best_goal_prob'] = 60 + int(min(35, spread_f * 2))
            
            if (h_exp - a_exp) > 8: preds['best_goal_pick'] = f"EV -{int((h_exp-a_exp)/2)}.5"
            elif (a_exp - h_exp) > 8: preds['best_goal_pick'] = f"DEP -{int((a_exp-h_exp)/2)}.5"

        # --- PROFESSOR SIMULATION ---
        if sport == 'basketball':
            sim_details = self.simulate_basketball_match(h_exp, a_exp, sport=sport)
        else:
            sim_details = self.simulate_match(h_exp, a_exp)
            
        preds['sim_details'] = sim_details

        # Additional Professor Logic: Period Predictions
        if sport == 'basketball':
            # Quarter/Half Logic
            preds['best_props_pick'] = f"1.YARI: {int((h_exp + a_exp) * 0.52)} ÜST"
            preds['best_props_prob'] = 65
            
            # Period Analysis (1. ve 3. çeyrekler genelde daha skorerdir EU'da)
            if "eur" in league_code:
                preds['best_props_pick'] += " | 3.ÇEYREK EN SKORER"

        preds['momentum'] = {'home': round(h_momentum, 2), 'away': round(a_momentum, 2)}
        preds['data_source'] = data_source

        # --- BARON SIGNALS 2.0: GLOBAL MARKET CONSENSUS ---
        if sofa_data and sofa_data.get('global_odds'):
            preds['global_market'] = sofa_data['global_odds']

        return preds


stat_engine = StatEngine()
sofa_adapter = SofaScoreAdapter()


def get_stat(team_data, abbr):
    for s in team_data.get('statistics', []):
        if s.get('abbreviation') == abbr:
            try: return float(s.get('displayValue'))
            except: return 0
    return 0


# --- CONFIGURATION: SUPPORTED LEAGUES ---
SUPPORTED_LEAGUES = [
    # --- MAJOR EUROPEAN ---
    {"name": "Premier League", "code": "eng.1", "sport": "soccer"},
    {"name": "La Liga", "code": "esp.1", "sport": "soccer"},
    {"name": "Bundesliga", "code": "ger.1", "sport": "soccer"},
    {"name": "Serie A", "code": "ita.1", "sport": "soccer"},
    {"name": "Ligue 1", "code": "fra.1", "sport": "soccer"},

    # --- TURKEY ---
    {"name": "Süper Lig", "code": "tur.1", "sport": "soccer", "sofascore_id": 52},
    {"name": "TFF 1. Lig", "code": "tur.2", "sport": "soccer", "sofascore_id": 53},

    # --- OTHER TOP LEAGUES ---
    {"name": "Eredivisie", "code": "ned.1", "sport": "soccer", "sofascore_id": 37},
    {"name": "Primeira Liga", "code": "por.1",
        "sport": "soccer", "sofascore_id": 238},
    {"name": "Championship", "code": "eng.2",
        "sport": "soccer", "sofascore_id": 18},
    {"name": "Serie B", "code": "ita.2", "sport": "soccer", "sofascore_id": 33},
    {"name": "2. Bundesliga", "code": "ger.2",
        "sport": "soccer", "sofascore_id": 44},
    {"name": "Belgian Pro League", "code": "bel.1",
        "sport": "soccer", "sofascore_id": 38},

    {"name": "Champions League", "code": "uefa.champions", "sport": "soccer"},
    {"name": "Europa League", "code": "uefa.europa", "sport": "soccer"},
    {"name": "Conference Lg", "code": "uefa.europa.conf", "sport": "soccer"},

    # --- BASKETBALL ---
    {"name": "NBA", "code": "nba", "sport": "basketball"},
    {"name": "EuroLeague", "code": "mens-euroleague", "sport": "basketball", "sofascore_id": 42527},
    {"name": "EuroCup", "code": "mens-eurocup", "sport": "basketball", "sofascore_id": 2560},
    {"name": "BSL", "code": "mens-turkish-super-league", "sport": "basketball", "sofascore_id": 595},
    {"name": "ACB", "code": "mens-spanish-liga-acb", "sport": "basketball", "sofascore_id": 271},
    {"name": "Lega A", "code": "mens-italian-lega-basket-serie-a", "sport": "basketball", "sofascore_id": 269},
    {"name": "Pro A", "code": "mens-french-lnb-pro-a", "sport": "basketball", "sofascore_id": 272},
    {"name": "BBL", "code": "mens-german-bbl", "sport": "basketball", "sofascore_id": 154}
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
    for i in range(1, 4):  # Yesterday, Day before, etc.
        target = today - timedelta(days=i)
        dates_to_fetch.append(target.strftime("%Y%m%d"))

    return fetch_matches_for_dates(dates_to_fetch, LEAGUES)


# --- STANDINGS API UPGRADE (Tier 1 Data) ---
STANDINGS_CACHE = {}
TEAM_ID_MAP = {} # Map team names to (id, league_code)


def fetch_standings(league_code, sport='soccer'):
    # Caching to avoid spamming API
    if league_code in STANDINGS_CACHE: return STANDINGS_CACHE[league_code]

    # ESPN API for Standings
    url = f"http://site.api.espn.com/apis/v2/sports/{sport}/{league_code}/standings"
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        if res.status_code == 200:
            data = res.json()
            team_stats = []

            children = data.get('children', [])
            if not children and 'standings' in data:
                 # Some basketball APIs have standings at top
                 entries = data.get('standings', {}).get('entries', [])
            elif children:
                # Common path
                entries = children[0].get('standings', {}).get('entries', [])
                # If NBA, maybe check all children
                if len(children) > 1 and league_code == 'nba':
                    for c in children[1:]:
                        entries.extend(c.get('standings', {}).get('entries', []))
            else:
                entries = []

            for entry in entries:
                    try:
                        team_data = entry.get('team', {})
                        display_name = team_data.get('displayName', '???')
                        
                        stats_list = entry.get('stats', [])
                        # Safety for rank access
                        rank_val = stats_list[0].get('value', 0) if stats_list else 0
                        
                        stats = {
                            'rank': rank_val,
                            'team': display_name,
                            'played': 0, 'w': 0, 'd': 0, 'l': 0, 'gf': 0, 'ga': 0, 'pts': 0
                        }
                        for s in stats_list:
                            name = s.get('name')
                            val = s.get('value', 0)
                            if name == 'rank': stats['rank'] = int(val)
                            if name == 'gamesPlayed': stats['played'] = int(val)
                            if name == 'wins': stats['w'] = int(val)
                            if name == 'draws': stats['d'] = int(val)
                            if name == 'losses': stats['l'] = int(val)
                            if name == 'pointsFor': stats['gf'] = int(val)
                            if name == 'pointsAgainst': stats['ga'] = int(val)
                            if name == 'points': stats['pts'] = int(val)
                        
                        team_stats.append(stats)
                        
                        # Cache Team ID for H2H fallback
                        t_id = team_data.get('id')
                        if display_name != '???' and t_id:
                            TEAM_ID_MAP[normalize_name(display_name)] = (t_id, league_code)
                            if 'shortDisplayName' in team_data:
                                TEAM_ID_MAP[normalize_name(team_data['shortDisplayName'])] = (t_id, league_code)
                    except Exception as te:
                        print(f"Entry Error: {te}")
                        continue

            print(f"Loaded Standings for {league_code}: {len(team_stats)} teams")
            STANDINGS_CACHE[league_code] = team_stats
            return team_stats
    except Exception as e:
        print(f"Standings Error {league_code}: {e}")

    STANDINGS_CACHE[league_code] = None
    return None

def fetch_h2h_data(event_id, home=None, away=None):
    if not event_id: return None
    
    if home and away:
        try:
            adapter = sofa_adapter
            resolved_id = adapter.get_event_id(home, away)
            if resolved_id:
                event_id = resolved_id
        except Exception:
            pass
    
    url = f"https://api.sofascore.com/api/v1/event/{event_id}/h2h"
    headers = {
        "Accept": "*/*",
        "X-Requested-With": "4795b7",
        "Origin": "https://www.sofascore.com",
        "Referer": "https://www.sofascore.com/"
    }
    
    try:
        res = sofa_adapter.scraper.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            matches_raw = data.get('events', [])
            h2h_list = []
            
            for m in matches_raw[:5]:
                dt = datetime.fromtimestamp(m.get('startTimestamp', 0)).strftime("%d.%m.%Y")
                h_name = m.get('homeTeam', {}).get('name', '???')
                a_name = m.get('awayTeam', {}).get('name', '???')
                h_score = m.get('homeScore', {}).get('current', 0)
                a_score = m.get('awayScore', {}).get('current', 0)
                
                h2h_list.append({
                    'date': dt,
                    'home': h_name,
                    'away': a_name,
                    'score': f"{h_score}-{a_score}"
                })
            return h2h_list
    except Exception:
        pass
    
    # --- ESPN FALLBACK ---
    try:
        h_norm = normalize_name(home)
        a_norm = normalize_name(away)
        h_info = None
        
        for name, info in TEAM_ID_MAP.items():
            if h_norm == name or h_norm in name or name in h_norm:
                h_info = info; break
        
        if h_info:
            t_id, l_code = h_info
            # Detect sport from league code OR from h_info if we decide to add it
            # For now, default to soccer but if l_code is nba, it's basketball
            sport = 'soccer'
            if l_code == 'nba' or 'mens-college-basketball' in l_code:
                 sport = 'basketball'
            
            url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{l_code}/teams/{t_id}/schedule"
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            if res.status_code == 200:
                data = res.json()
                events = data.get('events', [])
                h2h_list = []
                for e in events:
                    comps = e.get('competitions', [{}])
                    competitors = comps[0].get('competitors', [])
                    if len(competitors) < 2: continue
                    
                    # Check if score exists (means it's a past match)
                    h_team = next((c for c in competitors if c['homeAway'] == 'home'), {})
                    a_team = next((c for c in competitors if c['homeAway'] == 'away'), {})
                    
                    h_score = h_team.get('score', {}).get('displayValue')
                    a_score = a_team.get('score', {}).get('displayValue')
                    
                    if h_score is None or a_score is None: continue

                    # Look for opponent
                    opp = next((c for c in competitors if c['id'] != t_id), None)
                    if not opp: continue
                    
                    opp_norm = normalize_name(opp.get('team', {}).get('displayName', ''))
                    if a_norm in opp_norm or opp_norm in a_norm:
                        dt_raw = e.get('date', '')[:10]
                        dt = datetime.strptime(dt_raw, "%Y-%m-%d").strftime("%d.%m.%Y") if dt_raw else "???"
                        
                        h2h_list.append({
                            'date': dt,
                            'home': h_team.get('team', {}).get('displayName', '???'),
                            'away': a_team.get('team', {}).get('displayName', '???'),
                            'score': f"{h_score}-{a_score}"
                        })
                
                if h2h_list:
                    h2h_list.sort(key=lambda x: datetime.strptime(x['date'], "%d.%m.%Y"), reverse=True)
                    return h2h_list[:10]
    except Exception as e:
        print(f"H2H ESPN Fallback Error: {e}")

    return None


def fetch_matches_for_dates(dates_to_fetch, LEAGUES):
    print(
        f"DEBUG: STARTING FETCH for {len(LEAGUES)} leagues and {len(dates_to_fetch)} dates")
    matches = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    adapter = sofa_adapter # Use global instance for shared cache

    for league in LEAGUES:
        # Pre-fetch Standings for this league
        league_standings = fetch_standings(league['code'], league['sport'])

        for date_str in dates_to_fetch:
            url = f"http://site.api.espn.com/apis/site/v2/sports/{
    league['sport']}/{
        league['code']}/scoreboard?dates={date_str}"
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
                espn_event_ids = set()  # Track by name pattern

                # Add ESPN events first
                for ee in espn_events:
                    try:
                        competitors = ee.get('competitions', [{}])[
                                             0].get('competitors', [])
                        h = next(
                            (c['team']['name'] for c in competitors if c['homeAway'] == 'home'), "H")
                        a = next(
                            (c['team']['name'] for c in competitors if c['homeAway'] == 'away'), "A")
                        espn_event_ids.add(f"{h.lower()}-{a.lower()}")
                        final_events.append(ee)
                    except: pass

                # Fallback Discovery via SofaScore
                if league.get('sofascore_id'):
                    ss_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
                    ss_events = adapter.fetch_daily_fixtures(ss_date, sport=league['sport'])
                    target_id = league['sofascore_id']

                    added_count = 0
                    for se in ss_events:
                        t_name = se.get('tournament', {}).get('name', '').lower()
                        t_id = se.get('tournament', {}).get('id')
                        
                        # --- BASKETBALL FILTERS (Avoid Noise) ---
                        if league['sport'] == 'basketball':
                            noise_keywords = ["cyber", "esport", "simulated", "virtual", "women"]
                            if any(k in t_name for k in noise_keywords):
                                continue # Skip fake/women games for now unless requested
                                
                        # Match by ID or Name
                        is_match = False
                        if t_id and target_id and str(t_id) == str(target_id): 
                            is_match = True
                        elif "eurocup" in league['name'].lower() and "eurocup" in t_name:
                            is_match = True
                        elif "euroleague" in league['name'].lower() and "euroleague" in t_name:
                            is_match = True
                        elif "bsl" in league['name'].lower() and ("turkish basketball super league" in t_name or "bsl" in t_name):
                            is_match = True
                        elif "acb" in league['name'].lower() and ("acb" in t_name or "liga endesa" in t_name):
                            is_match = True
                        elif "lega a" in league['name'].lower() and ("lega a" in t_name or "italy" in t_name):
                            is_match = True
                        elif "pro a" in league['name'].lower() and ("pro a" in t_name or "lnb" in t_name):
                            is_match = True
                        elif "bbl" in league['name'].lower() and ("bbl" in t_name or "germany" in t_name):
                            is_match = True
                        
                        if is_match:
                            h_name = se['homeTeam']['name']
                            a_name = se['awayTeam']['name']

                            # Convert Timestamp to ESPN-like ISO format
                            ts = se.get('startTimestamp', 0)
                            dt_iso = datetime.fromtimestamp(ts).strftime("%Y-%m-%dT%H:%MZ") if ts else ""

                            # Skip if already in ESPN (simple check)
                            pattern = f"{h_name.lower()}-{a_name.lower()}"
                            if pattern in espn_event_ids: continue

                            # Fuzzy check (reversed or contains)
                            is_dup = False
                            for p in espn_event_ids:
                                if h_name.lower() in p and a_name.lower() in p:
                                    is_dup = True; break
                            if is_dup: continue

                            # Extract Form logic
                            h_recs = []
                            a_recs = []
                            
                            try:
                                h_form = se.get('homeTeamSeasonHistoricalForm', {})
                                if h_form and 'wins' in h_form and 'losses' in h_form:
                                    h_recs.append({'type': 'total', 'summary': f"{h_form['wins']}-{h_form['losses']}"})
                                
                                a_form = se.get('awayTeamSeasonHistoricalForm', {})
                                if a_form and 'wins' in a_form and 'losses' in a_form:
                                    a_recs.append({'type': 'total', 'summary': f"{a_form['wins']}-{a_form['losses']}"})
                            except: pass

                            # Convert to Synthetic Event
                            synthetic_event = {
                                'id': f"ss-{se['id']}",
                                'name': f"{h_name} vs {a_name}",
                                'date': dt_iso,
                                'status': {'type': {'state': 'pre', 'shortDetail': 'NS'}},
                                'competitions': [{
                                    'competitors': [
                                        {'homeAway': 'home', 'team': {
                                            'name': h_name}, 'score': '0', 'records': h_recs},
                                        {'homeAway': 'away', 'team': {
                                            'name': a_name}, 'score': '0', 'records': a_recs}
                                    ]
                                }]
                            }
                            # Map Status
                            ss_status = se.get('status', {}).get('type', '')
                            if ss_status == 'finished':
                                synthetic_event['status']['type']['state'] = 'post'
                                synthetic_event['status']['type']['shortDetail'] = 'FT'
                                synthetic_event['competitions'][0]['competitors'][0]['score'] = str(
                                    se.get('homeScore', {}).get('current', 0))
                                synthetic_event['competitions'][0]['competitors'][1]['score'] = str(
                                    se.get('awayScore', {}).get('current', 0))
                            elif ss_status == 'inprogress':
                                synthetic_event['status']['type']['state'] = 'in'
                                synthetic_event['status']['type'][
                                    'shortDetail'] = f"{se.get('status', {}).get('description', '45')}'"

                            final_events.append(synthetic_event)
                            added_count += 1

                    if added_count > 0:
                        print(
                            f"SofaScoreDiscovery: Added {added_count} matches for {league['name']} on {date_str}")
                    else:
                        print(f"SofaScoreDiscovery: No matches for {league['name']} in {len(ss_events)} events.")

                if not final_events: continue

                for event in final_events:
                    try:
                        competitions = event.get('competitions', [{}])[0]
                        competitors = competitions.get('competitors', [])

                        home_team = next(
                            (c['team']['name'] for c in competitors if c['homeAway'] == 'home'), "Home")
                        away_team = next(
                            (c['team']['name'] for c in competitors if c['homeAway'] == 'away'), "Away")

                        print(
                            f"DEBUG: {league['name']} | Match: {home_team} vs {away_team} | Date: {date_str}")

                        status_type = event.get('status', {}).get('type', {})
                        status_state = status_type.get(
                            'state')  # pre, in, post
                        status_detail = status_type.get('shortDetail')

                        home_score = next(
                            (c.get('score', '0') for c in competitors if c['homeAway'] == 'home'), '0')
                        away_score = next(
                            (c.get('score', '0') for c in competitors if c['homeAway'] == 'away'), '0')

                        sport = league['sport']

                        # --- WIN RATE EXTRACTION ---
                        def get_win_rate(records):
                            for r in records:
                                if r.get('type') == 'total':
                                    summary = r.get('summary', '0-0-0')
                                    try:
                                        parts = list(
                                            map(int, summary.split('-')))
                                        if len(parts) == 3:  # W-D-L (Soccer)
                                            w, d, l = parts
                                            total = w + d + l
                                        elif len(parts) == 2:  # W-L (Basketball)
                                            w, l = parts
                                            total = w + l
                                        else:
                                            return 0.40

                                        return w / total if total > 0 else 0.40
                                    except: return 0.40
                            return 0.40

                        home_rec = next(
                            (c.get('records', []) for c in competitors if c['homeAway'] == 'home'), [])
                        away_rec = next(
                            (c.get('records', []) for c in competitors if c['homeAway'] == 'away'), [])

                        home_win_rate = get_win_rate(home_rec)
                        away_win_rate = get_win_rate(away_rec)
                        
                        # --- STANDINGS LOOKUP (New GF/GA Data) ---
                        h_stats_real = None
                        a_stats_real = None

                        if league_standings:
                            # Search in list
                            for stand in league_standings:
                                s_team = stand['team'].lower()
                                normalize_s = normalize_name(s_team)
                                normalize_h = normalize_name(home_team)
                                normalize_a = normalize_name(away_team)
                                
                                if normalize_h in normalize_s or normalize_s in normalize_h:
                                    h_stats_real = stand
                                if normalize_a in normalize_s or normalize_s in normalize_a:
                                    a_stats_real = stand
                        
                        # Fallback for Win Rates if records are missing
                        if home_win_rate == 0.40 and h_stats_real:
                            h_w = h_stats_real.get('w', 0)
                            h_p = h_stats_real.get('played', 0)
                            if h_p > 0: home_win_rate = h_w / h_p
                            
                        if away_win_rate == 0.40 and a_stats_real:
                            a_w = a_stats_real.get('w', 0)
                            a_p = a_stats_real.get('played', 0)
                            if a_p > 0: away_win_rate = a_w / a_p

                        # --- LIVE STATS ---
                        live_stats = {'goals': 0, 'minute': 0}
                        try:
                            # Extract Minute
                            if status_state == 'in':
                                live_stats['minute'] = int(status_detail.replace(
                                    "'", "").split('+')[0]) if "'" in status_detail else 45

                            live_stats['goals'] = int(
                                home_score) + int(away_score)

                            # Extract Advanced Stats if available
                            home_data = next(
                                (c for c in competitors if c['homeAway'] == 'home'), {})
                            away_data = next(
                                (c for c in competitors if c['homeAway'] == 'away'), {})

                            live_stats['home_shots'] = get_stat(
                                home_data, 'SH')
                            live_stats['away_shots'] = get_stat(
                                away_data, 'SH')

                            live_stats['home_sot'] = get_stat(home_data, 'ST')
                            live_stats['away_sot'] = get_stat(away_data, 'ST')

                            live_stats['home_corners'] = get_stat(
                                home_data, 'CW')
                            live_stats['away_corners'] = get_stat(
                                away_data, 'CW')

                            live_stats['home_fouls'] = get_stat(
                                home_data, 'FC')
                            live_stats['away_fouls'] = get_stat(
                                away_data, 'FC')

                            live_stats['home_yc'] = get_stat(home_data, 'YC')
                            live_stats['away_yc'] = get_stat(away_data, 'YC')

                            h_p = get_stat(home_data, 'POS') or get_stat(
                                home_data, 'PP')
                            a_p = get_stat(away_data, 'POS') or get_stat(
                                away_data, 'PP')
                            if h_p + a_p > 0:
                                live_stats['home_pos'] = h_p
                                live_stats['away_pos'] = a_p

                        except: pass

                        # --- SOFASCORE LOOKUP & REFRESH ---
                        sofa_data = sofa_adapter.get_deep_stats(home_team, away_team)
                        
                        # If NOT found in adapter, try to discover it from ss_events
                        if not sofa_data and 'ss_events' in locals():
                            for se in ss_events:
                                if se.get('tournament', {}).get('id') == league.get('sofascore_id'):
                                    h_ss = se['homeTeam']['name']
                                    a_ss = se['awayTeam']['name']
                                    if (home_team.lower() in h_ss.lower() or h_ss.lower() in home_team.lower()) and \
                                       (away_team.lower() in a_ss.lower() or a_ss.lower() in away_team.lower()):
                                        # FOUND! Map it
                                        sofa_data = {
                                            'id': se['id'],
                                            'name': f"{h_ss} vs {a_ss}",
                                            'homeTeam': h_ss,
                                            'awayTeam': a_ss,
                                            'momentum_score': se.get('status', {}).get('description', ''),
                                            'league_id': se.get('tournament', {}).get('id')
                                        }
                                        # Save to adapter cache
                                        sofa_adapter.update_match_data(se['id'], sofa_data)
                                        break


                        # --- ODDS PARSING (MOVED UP FOR PREDICTION) ---
                        odds_data = competitions.get('odds', [])
                        bookie_home_odds = 0
                        bookie_away_odds = 0
                        spread = None
                        drop_info = None

                        # --- SOFASCORE SYNTHETIC ODDS INJECTION ---
                        # If this is a synthetic event (e.g. from SofaScore Discovery) and has no odds yet
                        if str(event.get('id', '')).startswith('ss-'):
                            try:
                                ssid = str(event['id']).replace('ss-', '')
                                ss_odds_data = adapter.get_odds(ssid)
                                if ss_odds_data and ss_odds_data.get('home') and ss_odds_data.get('away'):
                                    bookie_home_odds = ss_odds_data['home']
                                    bookie_away_odds = ss_odds_data['away']
                            except Exception as e:
                                print(f"SS Odds Injection Error: {e}")

                        if odds_data:
                            try:
                                provider = odds_data[0]
                                ml = {}
                                if isinstance(provider, dict):
                                    ml = provider.get('moneyline', {})
                                else:
                                    pass 

                                def am_to_dec(am_str):
                                       if not am_str: return 0
                                       try:
                                           val = float(am_str)
                                           if val > 0: return round(1 + (val / 100), 2)
                                           else: return round(1 + (100 / abs(val)), 2)
                                       except: return 0

                                if ml:
                                   bookie_home_odds = am_to_dec(
                                       ml.get('home', {}).get('current', {}).get('odds')) if bookie_home_odds == 0 else bookie_home_odds
                                   bookie_away_odds = am_to_dec(
                                       ml.get('away', {}).get('current', {}).get('odds')) if bookie_away_odds == 0 else bookie_away_odds

                                   # --- DROPPING ODDS ANALYSIS (BARON TRACKING) ---
                                   try:
                                       open_home = am_to_dec(
                                           ml.get('home', {}).get('open', {}).get('odds'))
                                       if open_home > 0 and bookie_home_odds > 0:
                                           drop_pct = (
                                               (open_home - bookie_home_odds) / open_home) * 100
                                           if drop_pct > 1.1: 
                                                drop_info = {'side': 'home', 'pct': round(
                                                    drop_pct, 1), 'open': open_home, 'curr': bookie_home_odds}

                                       open_away = am_to_dec(
                                           ml.get('away', {}).get('open', {}).get('odds'))
                                       if open_away > 0 and bookie_away_odds > 0:
                                           drop_pct = (
                                               (open_away - bookie_away_odds) / open_away) * 100
                                           if drop_pct > 1.1:
                                                drop_info = {'side': 'away', 'pct': round(
                                                    drop_pct, 1), 'open': open_away, 'curr': bookie_away_odds}
                                   except: pass

                            except: pass

                        # --- BLEND HISTORY WITH MARKET REALITY ---
                        # If market odds exist, use them to correct history
                        if bookie_home_odds > 1.0 and bookie_away_odds > 1.0:
                            market_h_prob = (1.0 / bookie_home_odds)
                            market_a_prob = (1.0 / bookie_away_odds)
                            # Normalize
                            total_m = market_h_prob + market_a_prob + (1.0 / 3.5) # rough draw
                            market_h_prob /= total_m
                            market_a_prob /= total_m
                            
                            # WEIGHTED BLEND: 40% History / 60% Market
                            home_win_rate = (home_win_rate * 0.40) + (market_h_prob * 0.60)
                            away_win_rate = (away_win_rate * 0.40) + (market_a_prob * 0.60)

                        # --- PRO PREDICTION GENERATION ---
                        # Pass real stats to engine
                        pro_stats = stat_engine.predict_match(
                            home_win_rate, away_win_rate, league["code"], sport,
                            home_team=home_team,
                            away_team=away_team,
                            live_stats=live_stats,
                            h_real=h_stats_real,
                            a_real=a_stats_real,
                            sofa_data=sofa_data
                        )

                        if sofa_data:
                            pro_stats['sofa_elite'] = sofa_data

                        # --- PROBABILITY CALC (Match Winner) ---
                        home_prob = home_win_rate * 1.10  # Home Adv
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



                        # --- SOFASCORE LOOKUP ---

                        # (Cleaned up: Dropping odds logic moved up)

                        # --- BARON SIGNALS 2.0: CROSS-MARKET CROSSOVER ---
                        if sofa_data and isinstance(sofa_data, dict) and sofa_data.get(
                            'global_odds') and bookie_home_odds > 0:
                            g_odds = sofa_data['global_odds']
                            g_home = g_odds.get('1')
                            if g_home and g_home > 0:
                                # If global price is SIGNIFICANTLY lower than local price, it's a "Signal"
                                # e.g. Bookie is 2.10, Global is 1.85
                                if bookie_home_odds > g_home * 1.05:
                                    market_lag = round(
                                        ((bookie_home_odds - g_home) / bookie_home_odds) * 100, 1)
                                    if not drop_info or market_lag > drop_info.get(
                                        'pct', 0):
                                         drop_info = {
                                             'side': 'home',
                                             'pct': market_lag,
                                             'open': bookie_home_odds,
                                             'curr': g_home,
                                             'type': 'GLOBAL_LAG'
                                         }
                                         pro_stats['recommendation'] = f"PİYASA DÜŞÜYOR ({market_lag}%)"
                                         pro_stats[
                                             'reasoning'] = f"Küresel piyasa {g_home} seviyesine çekildi. Yerel oran ({bookie_home_odds}) geride kaldı. FIRSAT!"

                        if bookie_home_odds == 0 or bookie_home_odds == "-":
                             h_p_safe = max(0.01, home_prob)
                             bookie_home_odds = round(
                                 max(1.05, min((1 / h_p_safe) / 1.05, 12.0)), 2)

                             away_p = max(0.01, 1.0 - home_prob)
                             bookie_away_odds = round(
                                 max(1.05, min((1 / away_p) / 1.05, 12.0)), 2)

                        if bookie_away_odds == 0: bookie_away_odds = "-"

                        # Extract Time
                        match_date = event.get('date', '')
                        display_time = status_detail

                        # If match is upcoming (Scheduled), show the actual
                        # Time (HH:MM)
                        if status_state == 'pre':
                            try:
                                # ESPN Date Format: 2023-10-25T19:00Z
                                dt = datetime.strptime(
                                    match_date, "%Y-%m-%dT%H:%MZ")
                                # Convert to Local Time (Assuming GMT+3 for
                                # Turkey Users)
                                dt = dt + timedelta(hours=3)
                                display_time = dt.strftime("%d.%m %H:%M")
                            except:
                                display_time = "Bekliyor"
                        else:
                                # Live or Completed
                                display_time = status_detail.replace(
                                    "Final", "Bitti").replace("Scheduled", "Bekliyor")

                        match = {
                            "id": event['id'],
                            "sport": sport,
                            "league": league["name"],
                            "home": home_team,
                                "away": away_team,
                                "time": display_time,
                            "status": "Live" if status_state == 'in' else "Completed" if status_state == 'post' else "Upcoming",
                            "score": f"{home_score}-{away_score}",
                            "odds": {"home": bookie_home_odds, "away": bookie_away_odds, "spread": spread},
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
                                 if "MS 1" in sys_rec:
                                     sys_rec = f"MS 1 ({spread})"
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
                                pass  # Stay PAS

                        # --- AI ADJUSTMENT (Learner Engine) ---
                        # Apply penalty/boost from model_weights.json
                        # sport code vs league code mapping? scraper uses
                        # 'league' field which matches baselines keys

                        # Note: 'league' variable holds the code e.g. 'eng.1'
                        if str(league) in stat_engine.learned_weights:
                            adj = stat_engine.learned_weights[str(league)].get(
                                'confidence_modifier', 0)
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
                                    l_code = AI_ENCODER.transform(
                                        [league["name"]])[0]
                                except:
                                    l_code = 0  # Unknown league (fallback)

                                # Handle Odds safely
                                h_o = float(bookie_home_odds) if isinstance(
                                    bookie_home_odds, (int, float)) else 1.50
                                a_o = float(bookie_away_odds) if isinstance(
                                    bookie_away_odds, (int, float)) else 1.50

                                features = pd.DataFrame([[l_code, h_o, a_o, sys_confidence]],
                                                      columns=['league_code', 'home_odds', 'away_odds', 'confidence'])

                                # Predict (Prob of Class 1: Win)
                                ai_prob = AI_MODEL.predict_proba(features)[
                                                                 0][1] * 100

                                # AI Insight Logic
                                if ai_prob > 75:
                                    ai_conf_boost = 10
                                    ai_note_text = f"YAPAY ZEKA ONAYLI (%{
    int(ai_prob)} Güven). Random Forest modeli bu maçı 'Kazanır' olarak görüyor."
                                elif ai_prob < 30:
                                    ai_conf_boost = -15
                                    ai_note_text = f"YAPAY ZEKA UYARISI (%{
    int(ai_prob)}). Model bu maça güvenmiyor."

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

                        market_vig = 0.05  # Standard bookie margin 5%

                        if isinstance(bookie_home_odds, (int, float)
                                      ) and bookie_home_odds > 1.0:
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
                             # Percentage of Bankroll
                             safe_stake = max(0, (kelly_fraction * 0.25) * 100)

                             edge = (real_prob - (1 / decimal_odds)) * 100

                             if safe_stake > 0 and edge > 0:
                                  match['value_found'] = True

                                  # Tiered Advice based on Stake Size
                                  stake_advice = "DÜŞÜK"
                                  if safe_stake > 4.0:
                                      stake_advice = "MAX (KASA)"
                                  elif safe_stake > 2.5: stake_advice = "YÜKSEK"
                                  elif safe_stake > 1.0: stake_advice = "ORTA"

                                  match['recommendation'] = f"{sys_rec} [STAKE %{
    safe_stake:.1f}]"
                                  if "KASA" in stake_advice:
                                       match['recommendation'] = f"💎 KASA: {
    match['recommendation']}"
                                  elif "YÜKSEK" in stake_advice:
                                       match['recommendation'] = f"🔥 BANKO: {
    match['recommendation']}"

                                  match['reasoning'] = (
                                      f"🧠 KELLY ANALİZİ: Kasanın %{
    safe_stake:.2f}'si Basılmalı.\n"
                                      f"📊 Matematiksel Avantaj (Edge): +%{
    edge:.1f}\n"
                                      f"🎯 Hedef Oran: {
    round(
        1 / real_prob,
         2)} | Alınan: {decimal_odds} | Güven: {stake_advice}"
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
                            f"🎰 MONTE CARLO SİMÜLASYONU (10.000 Maç):\n"
                            f"• Ev Sahibi: %{int(sim_data['home_win_prob'])}\n"
                            f"• Deplasman: %{int(sim_data['away_win_prob'])}\n"
                            f"• Beraberlik: %{int(sim_data['draw_prob'])}\n"
                            f"• 1.5 Üst: %{int(sim_data.get('over_1_5_prob', 0))}\n"
                            f"• 2.5 Üst: %{int(sim_data['over_2_5_prob'])}\n"
                            f"• KG Var: %{int(sim_data.get('btts_prob', 0))}"
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
