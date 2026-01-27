import requests
import json

def probe_espn():
    # Premier League as example
    url = "http://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard"
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        data = res.json()
        
        # Print the first event's competitor details to see if 'records' exists
        if data.get('events'):
            competitors = data['events'][0]['competitions'][0]['competitors']
            home = next(c for c in competitors if c['homeAway'] == 'home')
            print(json.dumps(home, indent=2))
        else:
            print("No events found to probe.")
    except Exception as e:
        print(e)

if __name__ == "__main__":
    probe_espn()
