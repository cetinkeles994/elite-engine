import json
import os
from flask import Flask, render_template, request, jsonify
import scraper_engine

app = Flask(__name__)

CACHE_FILE = "matches_cache.json"

def load_cached_matches():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

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
    matches = []
    
    if os.path.exists(HISTORY_CACHE_FILE):
        try:
            with open(HISTORY_CACHE_FILE, "r", encoding="utf-8") as f:
                matches = json.load(f)
        except:
             matches = []

    if sport_filter:
        matches = [m for m in matches if m.get('sport') == sport_filter]
    return jsonify(matches)

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

if __name__ == '__main__':
    app.run(debug=True)
