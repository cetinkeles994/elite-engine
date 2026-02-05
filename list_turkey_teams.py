import requests
import json

def list_all():
    # List all teams in tur.1
    url = "http://site.api.espn.com/apis/site/v2/sports/soccer/tur.1/teams"
    try:
        res = requests.get(url).json()
        teams = res.get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', [])
        print(f"Total Teams in tur.1: {len(teams)}")
        for t in teams:
            team = t.get('team', {})
            print(f"- {team.get('displayName')} (ID: {team.get('id')})")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    list_all()
