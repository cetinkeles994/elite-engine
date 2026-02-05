import requests
import json

def probe_more():
    # 1. List ALL teams in tur.1
    print("--- ALL TEAMS IN tur.1 ---")
    url_1 = "http://site.api.espn.com/apis/site/v2/sports/soccer/tur.1/teams"
    try:
        res = requests.get(url_1).json()
        teams = res.get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', [])
        for t in teams:
            print(f"  {t['team']['displayName']} (ID: {t['team']['id']})")
    except: print("tur.1 fetch failed")

    # 2. Iterate common codes to find TFF 1. Lig (tur.2, etc.)
    print("\n--- ITERATING LEAGUE CODES ---")
    codes = ["tur.1", "tur.2", "tur.3", "tur.cup", "tur.lig", "tur.tff", "tur.1_lig", "tur.2_lig"]
    for c in codes:
        url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{c}/teams"
        try:
            res = requests.get(url, timeout=3).json()
            league_name = res.get('sports', [{}])[0].get('leagues', [{}])[0].get('name', 'N/A')
            team_count = len(res.get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', []))
            print(f"Code: {c} | Name: {league_name} | Teams: {team_count}")
        except: pass

    # 3. Check Besiktas Schedule
    print("\n--- BESIKTAS SCHEDULE (ID: 1895) ---")
    url_b = "http://site.api.espn.com/apis/site/v2/sports/soccer/scoreboard?teams=1895&dates=20260120-20260210"
    try:
        res = requests.get(url_b).json()
        events = res.get('events', [])
        for e in events:
            league_id = e.get('league', {}).get('id', 'N/A')
            league_code = e.get('season', {}).get('slug', 'N/A')
            print(f"Match: {e['name']} | Date: {e['date']} | League ID: {league_id}")
    except: print("Besiktas schedule failed")

if __name__ == '__main__':
    probe_more()
