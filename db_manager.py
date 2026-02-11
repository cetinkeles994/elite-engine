import sqlite3
import json
import os
from datetime import datetime

DB_PATH = "kahin_data.db"

class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Matches Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS matches (
                    id TEXT PRIMARY KEY,
                    league TEXT,
                    home TEXT,
                    away TEXT,
                    sport TEXT,
                    status TEXT,
                    score TEXT,
                    prediction_json TEXT,
                    last_update DATETIME
                )
            """)
            
            # 2. History Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id TEXT PRIMARY KEY,
                    match_id TEXT,
                    final_result TEXT,
                    result_status TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 3. Team Mappings Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS team_mappings (
                    team_name TEXT PRIMARY KEY,
                    sofascore_id INTEGER,
                    espn_slug TEXT
                )
            """)
            
            conn.commit()

    def upsert_match(self, match_data):
        """
        Inserts or updates a match in the database.
        match_data is a dict containing all match info.
        """
        match_id = match_data.get('id')
        if not match_id: return
        
        # Serialize the full dict as JSON for flexibility, but keep core fields for querying
        prediction_json = json.dumps(match_data, ensure_ascii=False)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO matches (id, league, home, away, sport, status, score, prediction_json, last_update)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status=excluded.status,
                    score=excluded.score,
                    prediction_json=excluded.prediction_json,
                    last_update=excluded.last_update
            """, (
                match_id,
                match_data.get('league'),
                match_data.get('home'),
                match_data.get('away'),
                match_data.get('sport', 'soccer'),
                match_data.get('status'),
                match_data.get('score'),
                prediction_json,
                datetime.now()
            ))
            conn.commit()

    def save_matches_batch(self, matches_list):
        for m in matches_list:
            self.upsert_match(m)

    def get_all_matches(self):
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT prediction_json FROM matches")
            rows = cursor.fetchall()
            return [json.loads(row['prediction_json']) for row in rows]

    def get_success_report(self):
        """Calculates win rate for finished matches."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # Select matches that are finished and have a goal_pick_result
            cursor.execute("SELECT prediction_json FROM matches WHERE status='Finished'")
            rows = cursor.fetchall()
            
            total = 0
            wins = 0
            
            for row in rows:
                data = json.loads(row['prediction_json'])
                res = data.get('goal_pick_result')
                if res:
                    total += 1
                    if res == 'won': wins += 1
            
            win_rate = (wins / total * 100) if total > 0 else 0
            return {
                'total_analyzed': total,
                'wins': wins,
                'win_rate': round(win_rate, 1)
            }

db_manager = DatabaseManager()
