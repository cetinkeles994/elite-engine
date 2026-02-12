import json
import os
from flask import Flask, render_template, request, jsonify
import scraper_engine

app = Flask(__name__)

CACHE_FILE = "matches_cache.json"

from db_manager import db_manager

def load_cached_matches():
    return db_manager.get_active_matches()

@app.route('/')
def dashboard():
    matches = load_cached_matches()
    return render_template('dashboard.html', matches=matches)

@app.route('/api/fixtures')
def api_fixtures():
    sport_filter = request.args.get('sport') # 'soccer' or 'basketball'
    matches = load_cached_matches()
    
    if sport_filter:
        matches = [m for m in matches if m.get('sport') == sport_filter]
        
    return jsonify(matches)

HISTORY_CACHE_FILE = "history_cache.json"

@app.route('/api/history')
def api_history():
    sport_filter = request.args.get('sport')
    # Use ALL matches from DB for history, filtering by Finished status
    all_matches = db_manager.get_all_matches() 
    history_matches = [m for m in all_matches if m.get('status') == 'Finished' or m.get('result') != 'pending']
    
    if sport_filter:
        history_matches = [m for m in history_matches if m.get('sport') == sport_filter]
    return jsonify(history_matches)

from ai_chat import MatchChatBot
chatbot = MatchChatBot()

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.json
    message = data.get('message', '')
    session_id = data.get('sessionId', 'default') # Support session tracking
    
    if not message:
        return jsonify({'response': "Lütfen bir şeyler yazın."})
    
    response_html = chatbot.execute(message, session_id=session_id)
    return jsonify({'response': response_html})

@app.route('/api/standings/<league_code>')
def api_standings(league_code):
    data = scraper_engine.fetch_standings(league_code)
    return jsonify(data)

@app.route('/api/h2h/<event_id>')
def api_h2h(event_id):
    home = request.args.get('home')
    away = request.args.get('away')
    data = scraper_engine.fetch_h2h_data(event_id, home=home, away=away)
    return jsonify(data)

@app.route('/api/coupons')
def api_coupons():
    matches = load_cached_matches()
    # Filter only soccer matches and only upcoming/live
    soccer_matches = [m for m in matches if m.get('sport') == 'soccer' and m.get('status') != 'Completed']
    
    if not soccer_matches:
        return jsonify([])

    used_ids = set()
    
    def get_best_for_market(market_key, min_prob=70):
        best_match = None
        best_prob = 0
        
        for m in soccer_matches:
            if m['id'] in used_ids: continue
            
            pro = m.get('pro_stats', {})
            sim = pro.get('sim_details', {})
            
            prob = 0
            if market_key == '1.5_UST': prob = sim.get('over_1_5_prob', 0)
            elif market_key == '2.5_UST': prob = sim.get('over_2_5_prob', 0)
            elif market_key == 'KG_VAR': prob = sim.get('btts_prob', 0)
            elif market_key == 'MS': 
                # Highest winning prob (either home or away)
                h_p = sim.get('home_win_prob', 0)
                a_p = sim.get('away_win_prob', 0)
                prob = max(h_p, a_p)
            
            if prob > min_prob and prob > best_prob:
                best_prob = prob
                best_match = m
        
        if best_match:
            used_ids.add(best_match['id'])
            # Add specific market info to the returned match
            market_map = {
                '1.5_UST': '1.5 ÜST',
                '2.5_UST': '2.5 ÜST',
                'KG_VAR': 'KG VAR',
                'MS': 'MS 1' if sim.get('home_win_prob', 0) > sim.get('away_win_prob', 0) else 'MS 2'
            }
            best_match['coupon_pick'] = market_map[market_key]
            best_match['coupon_prob'] = int(best_prob)
            
        return best_match

    # Generate 3 Unique Coupons
    coupons = []
    for i in range(3):
        coupon = []
        # Try to pick one from each category for each coupon
        for cat in ['1.5_UST', '2.5_UST', 'KG_VAR', 'MS']:
            m = get_best_for_market(cat, min_prob=65)
            if m:
                # We need to copy to avoid mutation issues if same match is picked (though used_ids prevents it)
                m_copy = json.loads(json.dumps(m))
                coupon.append(m_copy)
        
        if coupon:
            coupons.append({
                "id": i + 1,
                "name": f"KAHİN KUPONU #{i+1}",
                "matches": coupon,
                "total_odds": round(sum([float(x.get('odds', {}).get('home', 1.5)) for x in coupon]) / len(coupon) * 2.5, 2) # Mock odds calc
            })
            
    return jsonify(coupons)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
