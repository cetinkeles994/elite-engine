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
                    self.data_map = json.load(f)
            except Exception as e:
                print(f"SofaScore Cache Load Error: {e}")
                self.data_map = {}

    def save_cache(self):
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.data_map, f, indent=4, ensure_ascii=False)
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

# Usage Example
if __name__ == "__main__":
    adapter = SofaScoreAdapter()
    print("SofaScore Adapter Initialized.")
