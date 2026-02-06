
from sofascore_adapter import SofaScoreAdapter

adapter = SofaScoreAdapter()
event_id = '14116713'
print(f"Fetching odds for {event_id}...")
odds = adapter.get_odds(event_id)
print(f"Result: {odds}")
