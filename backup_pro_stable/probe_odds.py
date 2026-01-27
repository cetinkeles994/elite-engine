import requests
import json

def probe_odds():
    # Premier League often has odds
    url = "http://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard"
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        data = res.json()
        
        if data.get('events'):
            # Check first 5 events for ANY odds data
            for event in data['events'][:5]:
                competitions = event.get('competitions', [{}])[0]
                odds = competitions.get('odds')
                if odds:
                    print(f"\n--- Odds Found for {event['name']} ---")
                    print(json.dumps(odds, indent=2))
                else:
                    print(f"No odds for {event['name']}")
    except Exception as e:
        print(e)

if __name__ == "__main__":
    probe_odds()
