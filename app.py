import json
import os
from flask import Flask, render_template, request, jsonify

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

@app.route('/api/history')
def api_history():
    sport_filter = request.args.get('sport')
    matches = scrape_history()
    if sport_filter:
        matches = [m for m in matches if m.get('sport') == sport_filter]
    return jsonify(matches)

if __name__ == '__main__':
    app.run(debug=True)
