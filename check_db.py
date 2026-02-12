import sqlite3
import json
from datetime import datetime

with sqlite3.connect("kahin_data.db") as conn:
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT prediction_json FROM matches LIMIT 30")
    rows = cursor.fetchall()
    for row in rows:
        m = json.loads(row['prediction_json'])
        print(f"ID: {m.get('id')} | Time: {m.get('time')} | Status: {m.get('status')} | Score: {m.get('score')}")
