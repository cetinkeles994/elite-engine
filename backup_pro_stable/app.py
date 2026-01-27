from flask import Flask, render_template, request, jsonify
from flask import Flask, render_template, request, jsonify
from scraper_engine import scrape_todays_fixtures, scrape_history

app = Flask(__name__)

# Cache for global matches (to avoid spamming scraper)
global_matches_cache = []

@app.route('/')
def dashboard():
    # In a real app, you would use a background scheduler (apscheduler) to update this cache.
    # For this demo, we fetch on load (simulated scraper is fast).
    global_matches = scrape_todays_fixtures()
    return render_template('dashboard.html', matches=global_matches)

@app.route('/api/fixtures')
def api_fixtures():
    # JSON endpoint for auto-refresh via AJAX
    sport_filter = request.args.get('sport') # 'soccer' or 'basketball'
    matches = scrape_todays_fixtures()
    
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
