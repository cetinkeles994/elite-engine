
from sofascore_adapter import SofaScoreAdapter
import json

adapter = SofaScoreAdapter()
# Use a date that definitely has matches, e.g. 2026-02-08 from logs
date_str = "2026-02-08"
print(f"Fetching events for {date_str}...")
events = adapter.fetch_daily_fixtures(date_str, sport="basketball")

if events:
    print(f"Fetched {len(events)} events.")
    print("Sample Event Keys:", events[0].keys())
    # Check if any event has 'odds'
    has_odds = any('odds' in e for e in events)
    print(f"Any event has 'odds'? {has_odds}")
    
    # Dump one event
    print(json.dumps(events[0], indent=2))
else:
    print("No events found.")
