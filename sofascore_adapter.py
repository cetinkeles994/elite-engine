import json
import os
import requests
import re
import cloudscraper
from datetime import datetime

class SofaScoreAdapter:
    def __init__(self, cache_file="sofascore_data.json"):
        self.cache_file = cache_file
        self.data_map = {}
        self.team_ids = {} # Cache for team names -> IDs
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        self.load_cache()

    def load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    all_data = json.load(f)
                    # If the file has the new format {events: {}, teams: {}}
                    if isinstance(all_data, dict) and 'events' in all_data:
                        self.data_map = all_data.get('events', {})
                        self.team_ids = all_data.get('teams', {})
                    else:
                        # Legacy format (just the event map)
                        self.data_map = all_data
                        self.team_ids = {}
            except Exception as e:
                print(f"SofaScore Cache Load Error: {e}")
                self.data_map = {}

    def save_cache(self):
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump({
                    'events': self.data_map,
                    'teams': self.team_ids
                }, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"SofaScore Cache Save Error: {e}")

    def get_event_id(self, home_team, away_team):
        """
        Attempts to find a SofaScore eventId for a match by fuzzy matching team names.
        """
        home_team = home_team.lower()
        away_team = away_team.lower()
        
        for event_id, data in self.data_map.items():
            if not isinstance(data, dict): continue
            
            # Check the "name" field or homeTeam/awayTeam fields
            match_name = str(data.get('name', '')).lower()
            
            h_data = data.get('homeTeam', '')
            if isinstance(h_data, dict): h_data = h_data.get('name', '')
            h_data = str(h_data).lower()
            
            a_data = data.get('awayTeam', '')
            if isinstance(a_data, dict): a_data = a_data.get('name', '')
            a_data = str(a_data).lower()
            
            # If both teams are in the cached match name or specific fields
            if (home_team in match_name and away_team in match_name) or \
               (home_team in h_data and away_team in a_data):
                return event_id
        return None

    def get_deep_stats(self, home_team, away_team):
        """
        Returns deep stats (xG, momentum, etc.) if available in cache.
        """
        event_id = self.get_event_id(home_team, away_team)
        if not event_id:
            return None
        
        return self.data_map.get(str(event_id))

    def fractional_to_decimal(self, frac_str):
        """
        Converts fractional odds (e.g., '15/4') to decimal (e.g., 4.75)
        """
        try:
            if not frac_str: return 0.0
            if '/' not in frac_str: return float(frac_str)
            num, den = map(float, frac_str.split('/'))
            return round((num / den) + 1, 2)
        except:
            return 0.0

    def parse_market_odds(self, markets):
        """
        Extracts 1X2 odds from a list of markets.
        """
        odds = {}
        for market in markets:
            if market.get('marketName') == 'Full time' and market.get('choiceGroup') is None:
                choices = market.get('choices', [])
                for choice in choices:
                    name = choice.get('name')
                    val = self.fractional_to_decimal(choice.get('fractionalValue'))
                    if name in ['1', 'X', '2']:
                        odds[name] = val
        return odds

    def update_match_data(self, event_id, stats):
        """
        Updates the cache with new deep stats.
        """
        self.data_map[str(event_id)] = stats
        self.save_cache()

    def reset_cache(self):
        """ Clears the in-memory data map. """
        self.data_map = {}

    def fetch_daily_fixtures(self, date_str, sport='football'):
        """
        Fetches all events for a specific date from SofaScore for a given sport.
        Format: YYYY-MM-DD
        """
        # Ensure date format is YYYY-MM-DD
        if len(date_str) == 8 and '-' not in date_str:
            date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"

        urls = [
            f"http://api.sofascore.com/api/v1/sport/{sport}/scheduled-events/{date_str}",
            f"http://www.sofascore.com/api/v1/sport/{sport}/scheduled-events/{date_str}"
        ]
        headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Referer": "https://www.sofascore.com/",
            "Origin": "https://www.sofascore.com",
            "Accept-Language": "en-US,en;q=0.9"
        }
        for url in urls:
            try:
                # Try raw requests for http (less likely to be blocked by TLS fingerprinters)
                if url.startswith("http://"):
                    res = requests.get(url, headers=headers, timeout=15)
                else:
                    res = self.scraper.get(url, headers=headers, timeout=15)
                if res.status_code == 200:
                    data = res.json()
                    events = data.get('events', [])
                    print(f"SofaScore: Fetched {len(events)} {sport} events for {date_str}")
                    return events
                else:
                    print(f"SofaScore Fetch Failed ({url}): {res.status_code}")
            except Exception as e:
                print(f"SofaScore Fetch Error ({url}): {e}")
        return []

    def get_odds(self, event_id):
        """
        Fetches odds for a specific event. Returns dict with '1', 'X', '2' keys (decimal).
        """
        urls = [
            f"https://api.sofascore.com/api/v1/event/{event_id}/odds/1/all",
            f"http://api.sofascore.com/api/v1/event/{event_id}/odds/1/all",
            f"https://www.sofascore.com/api/v1/event/{event_id}/odds/1/all"
        ]
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Referer": "https://www.sofascore.com/",
            "Origin": "https://www.sofascore.com",
            "Accept": "*/*"
        }
        
        for url in urls:
            try:
                 res = self.scraper.get(url, headers=headers, timeout=10)
                 if res.status_code == 200:
                     data = res.json()
                     markets = data.get('markets', [])
                     parsed = self.parse_market_odds(markets)
                     
                     # Convert keys to home/away for easier consumption
                     ret = {}
                     if '1' in parsed: ret['home'] = parsed['1']
                     if '2' in parsed: ret['away'] = parsed['2']
                     if 'X' in parsed: ret['draw'] = parsed['X']
                     
                     if ret: return ret # Only return if we actually got something
                     
            except Exception as e:
                 print(f"Odds Fetch Attempt Error ({url}): {e}")
        
        return None

    def find_team_id(self, team_name):
        """
        Searches for a team ID on SofaScore.
        """
        if team_name in self.team_ids:
            return self.team_ids[team_name]
            
        url = f"https://api.sofascore.com/api/v1/search/all?q={team_name}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Referer": "https://www.sofascore.com/"
        }
        try:
            res = self.scraper.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                results = res.json().get('results', [])
                for r in results:
                    if r.get('type') == 'team':
                        t_id = r.get('entity', {}).get('id')
                        self.team_ids[team_name] = t_id
                        self.save_cache()
                        return t_id
        except Exception as e:
            print(f"Team Search Error ({team_name}): {e}")
        return None

    def get_missing_players(self, event_id):
        """
        Fetches missing players (injuries/suspensions) for a specific event.
        """
        urls = [
            f"http://api.sofascore.com/api/v1/event/{event_id}/missing-players",
            f"https://api.sofascore.com/api/v1/event/{event_id}/missing-players"
        ]
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.sofascore.com/"
        }
        for url in urls:
            try:
                res = self.scraper.get(url, headers=headers, timeout=10)
                if res.status_code == 200:
                    return res.json()
            except: pass
        return None

    def get_team_form(self, team_id):
        """
        Fetches the last 5 match results for a team.
        Returns (form_string, form_score)
        """
        if not team_id: return "", 0
        
        # Note: We use last/0 but we could try to be more specific if sport matters
        url = f"https://api.sofascore.com/api/v1/team/{team_id}/events/last/0" 
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Referer": "https://www.sofascore.com/"
        }
        
        try:
            res = self.scraper.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                events = res.json().get('events', [])
                form_chars = []
                score = 0
                
                # Process last 5 finished events
                finished_count = 0
                for ev in events:
                    if finished_count >= 5: break
                    if ev.get('status', {}).get('type') != 'finished': continue
                    
                    winner_code = ev.get('winnerCode') # 1: Home, 2: Away, 3: Draw
                    is_home = ev.get('homeTeam', {}).get('id') == team_id
                    
                    if winner_code == 3:
                        form_chars.append('D')
                        score += 0.5
                    elif (is_home and winner_code == 1) or (not is_home and winner_code == 2):
                        form_chars.append('W')
                        score += 1.0
                    else:
                        form_chars.append('L')
                        score -= 0.5 # Losses are heavy
                    
                    finished_count += 1
                
                # Order from oldest to newest or vice-versa? 
                # Usually left is oldest, right is newest: "L-W-D-W-W"
                # The API returns them newest first, so we reverse.
                form_chars.reverse()
                return "-".join(form_chars), score
                
        except Exception as e:
            print(f"Team Form Error (ID {team_id}): {e}")
            
        return "", 0

# Usage Example
if __name__ == "__main__":
    adapter = SofaScoreAdapter()
    print("SofaScore Adapter Initialized.")
