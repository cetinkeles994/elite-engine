import requests
import json

def probe():
    # Premier League (17) - Season 52186 (23/24) - Example IDs
    # We need to find the CURRENT season ID dynamically usually, but lets try a known one or discover it.
    
    # Premier League Unique Tournament ID: 17
    # Season ID: 61627 (24/25) - Estimated
    
    url = "https://api.sofascore.com/api/v1/unique-tournament/17/season/61627/standings/total"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://www.sofascore.com/"
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=5)
        print(f"Status Code: {res.status_code}")
        
        if res.status_code == 200:
            data = res.json()
            standings = data.get('standings', [])
            if standings:
                table = standings[0]
                print(f"Type: {table.get('type')}")
                rows = table.get('rows', [])
                if rows:
                    row = rows[0]
                    team = row.get('team', {}).get('name')
                    print(f"First Team: {team}")
                    print("Stats Available Keys:", row.get('matches', 0), row.keys())
                    # Check for splits
                    print("Home/Away Split Check: ", row.get('home'), row.get('away'))
            else:
                print("No standings found.")
        else:
            print("Failed to fetch.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    probe()
