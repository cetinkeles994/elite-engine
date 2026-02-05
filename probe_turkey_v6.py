import requests
import json

def search():
    dates = ["20260131", "20260201", "20260202"]
    codes = ["tur.1", "tur.2", "tur.cup", "tur.super_lig"]
    targets = ["Besiktas", "Adana", "Bolu", "Amed", "Demirspor"]
    
    print("--- COMPREHENSIVE TURKEY PROBE v6 ---")
    
    for d in dates:
        print(f"\n>>> DATE: {d}")
        # Global search
        try:
            url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/scoreboard?dates={d}"
            res = requests.get(url, timeout=5).json()
            events = res.get('events', [])
            print(f"Global events: {len(events)}")
            for e in events:
                name = e.get('name', '')
                if any(t.lower() in name.lower() for t in targets):
                    print(f"  [GLOBAL FOUND] {name} | League ID: {e.get('league', {}).get('id', 'N/A')}")
        except: pass

        # League specific
        for c in codes:
            try:
                url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{c}/scoreboard?dates={d}"
                res = requests.get(url, timeout=5).json()
                l_name = res.get('leagues', [{}])[0].get('name', 'N/A')
                events = res.get('events', [])
                if events:
                    print(f"  [{c}] {l_name}: {len(events)} events")
                    for ev in events:
                        name = ev.get('name', '')
                        print(f"    - {name}")
                if any(any(t.lower() in ev.get('name', '').lower() for t in targets) for ev in events):
                    print(f"    *** TARGET MATCH IN {c} ***")
            except: pass

if __name__ == '__main__':
    search()
