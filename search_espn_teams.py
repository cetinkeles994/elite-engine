import requests
import json

def search_espn(query):
    url = f"https://site.api.espn.com/apis/search/v2/sports/soccer/suggest?query={query}"
    try:
        res = requests.get(url, timeout=5).json()
        suggestions = res.get('suggestions', [])
        print(f"\n--- SEARCH: {query} ---")
        for s in suggestions:
            for item in s.get('items', []):
                print(f"  {item.get('displayName')} | ID: {item.get('id')} | Type: {item.get('type')}")
    except:
        print(f"Search for {query} failed")

if __name__ == '__main__':
    search_espn("Amed")
    search_espn("Boluspor")
    search_espn("Adana Demirspor")
    search_espn("Amed SK")
    search_espn("Bodrumspor")
    search_espn("Kasımpaşa")
