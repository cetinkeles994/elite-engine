import json

def parse_sofascore_dump(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    events = data.get('events', [])
    print(f"Total events: {len(events)}")
    
    turkish = []
    for e in events:
        tournament = e.get('tournament', {})
        category = tournament.get('category', {}).get('name')
        if category in ['Turkey', 'Türki̇ye', 'Turkiye']:
            turkish.append({
                'name': e['name'],
                'tournament': tournament['name'],
                'id': e['id'],
                'tournament_id': tournament.get('uniqueTournament', {}).get('id', tournament.get('id')),
                'time': e.get('startTimestamp')
            })
    
    print(f"\n--- TURKISH MATCHES FOUND ({len(turkish)}) ---")
    for m in turkish:
        print(f"Match: {m['name']} | League: {m['tournament']} (ID: {m['tournament_id']})")

if __name__ == '__main__':
    # Since I can't easily piping read_url_content to a file, I'll use a small script 
    # that I will paste the content into IF I had it. 
    # But wait, I can just RE-RUN a script that fetches it using requests 
    # but maybe with the tool-discovered headers? 
    # No, I'll just use the tool again and pipe to a file if possible? 
    # Wait, I can't pipe tools.
    
    # I'll just perform a GREP-like search on the previous tool output in my mind.
    pass
