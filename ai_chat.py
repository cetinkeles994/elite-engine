import json
import re

class MatchChatBot:
    def __init__(self, cache_file="matches_cache.json"):
        self.cache_file = cache_file
        self.matches = []
        self.load_data()

    def load_data(self):
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                self.matches = json.load(f)
            print(f"ChatBot Loaded {len(self.matches)} matches.")
        except Exception as e:
            print(f"ChatBot Load Error: {e}")
            self.matches = []

    def parse_query(self, query):
        """
        Parses Turkish natural language query.
        Returns filters dict: { 'limit': 5, 'type': 'over_2_5', 'sort': 'confidence' }
        """
        q = query.lower()
        filters = {
            'limit': 3, # Default
            'type': 'any',
            'sort': 'confidence', # Default sort by AI confidence
            'min_prob': 0
        }

        # 1. EXTRACT LIMIT (e.g. "5 tane", "top 10", "tek maç")
        # Look for numbers
        num_match = re.search(r'(\d+)\s*(adet|tane|maç)?', q)
        if num_match:
            try:
                val = int(num_match.group(1))
                if 0 < val < 20: filters['limit'] = val
            except: pass
        
        if "tek maç" in q: filters['limit'] = 1

        # 2. EXTRACT INTENT / TYPE
        # Over/Under
        if "üst" in q or "over" in q:
            if "1.5" in q: filters['type'] = "over_1_5"
            elif "3.5" in q: filters['type'] = "over_3_5"
            else: filters['type'] = "over_2_5" # Default "üst" = 2.5
        elif "alt" in q or "under" in q:
            filters['type'] = "under_2_5"
        
        # BTTS (KG)
        elif "kg var" in q or "karşılıklı gol" in q: filters['type'] = "btts_yes"
        elif "kg yok" in q: filters['type'] = "btts_no"

        # Side (Home/Away/Banko)
        elif "banko" in q or "güvenilir" in q or "en iyi" in q:
            filters['type'] = "banko"
            filters['min_prob'] = 65
        elif "sürpriz" in q or "oranı yüksek" in q:
            filters['type'] = "surprise"
            filters['sort'] = 'odds_desc'

        # Home/Away specific
        elif "ev sahibi" in q or "ms 1" in q: filters['type'] = "home_win"
        elif "deplasman" in q or "ms 2" in q: filters['type'] = "away_win"
        
        # Specific Teams
        # (Basic implementation: check if query contains known team names?)
        # For now, we focus on filtering types.

        return filters

    def execute(self, query):
        self.load_data() # Refresh cache
        filters = self.parse_query(query)
        
        results = []

        for m in self.matches:
            # Safely get stats
            ps = m.get('pro_stats', {})
            rec = m.get('recommendation', '')
            
            # --- FILTERING LOGIC ---
            
            # 1. Banko / General Confidence
            if filters['type'] == 'banko':
                # Must be a recommended pick or high prob
                valid = False
                if "KASA" in rec or "BANKO" in rec: valid = True
                if ps.get('best_goal_prob', 0) > 70: valid = True
                if not valid: continue
            
            # 2. Over/Under
            elif filters['type'].startswith('over_'):
                pick = ps.get('best_goal_pick', '')
                if filters['type'] == 'over_2_5' and "2.5 ÜST" not in pick: continue
                if filters['type'] == 'over_1_5' and "1.5 ÜST" not in pick: continue
                if filters['type'] == 'over_3_5' and "3.5 ÜST" not in pick: continue
            
            elif filters['type'].startswith('under_'):
                 pick = ps.get('best_goal_pick', '')
                 if "ALT" not in pick: continue

            # 3. BTTS
            elif filters['type'] == 'btts_yes':
                if "KG VAR" not in ps.get('best_goal_pick', ''): continue
            
            # 4. Surprise
            elif filters['type'] == 'surprise':
                # Look for odds > 2.00
                try:
                    h_o = float(m['odds']['home'])
                    a_o = float(m['odds']['away'])
                    if h_o < 2.0 and a_o < 2.0: continue
                except: continue

            # 5. Side
            elif filters['type'] == 'home_win':
                if "MS 1" not in rec: continue
            elif filters['type'] == 'away_win':
                if "MS 2" not in rec: continue

            # ADD TO RESULTS
            # Calculate a "Score" for sorting
            score = 0
            
            # Use Reliability/Confidence
            if "KASA" in rec: score += 100
            elif "BANKO" in rec: score += 80
            
            # Goal Prob
            score += ps.get('best_goal_prob', 50)
            
            results.append({
                'match': m,
                'score': score
            })

        # --- SORTING ---
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # --- LIMIT ---
        final_list = results[:filters['limit']]
        
        return self.format_response(final_list, filters)

    def format_response(self, results, filters):
        if not results:
            return "Maalesef kriterlerine uygun maç bulamadım. Daha genel bir şeyler sormayı dene (örn: 'Banko maçlar')."
        
        html = f"<div class='chat-response-header'>İşte senin için bulduğum {len(results)} maç:</div>"
        
        for item in results:
            m = item['match']
            ps = m.get('pro_stats', {})
            
            # Mini Card Design
            card = f"""
            <div class="chat-card bg-gray-800 p-2 rounded mb-2 border border-gray-700 hover:border-blue-500 cursor-pointer transition-colors" onclick="openModalMatch('{m['id']}')">
                <div class="flex justify-between items-center mb-1">
                    <span class="text-xs text-gray-400">{m['league']}</span>
                    <span class="text-xs font-bold text-green-400">{m['time']}</span>
                </div>
                <div class="font-bold text-sm text-white">{m['home']} vs {m['away']}</div>
                <div class="mt-1 flex gap-2 text-xs">
                    <span class="px-1 bg-blue-900 rounded text-blue-200">Tahmin: {m['recommendation'].replace('💎 KASA:', '').replace('🔥 BANKO:', '')}</span>
                    <span class="px-1 bg-gray-700 rounded text-gray-300">Oran: {m['odds']['home']} - {m['odds']['away']}</span>
                </div>
            </div>
            """
            html += card
            
        return html

if __name__ == "__main__":
    # Test
    bot = MatchChatBot()
    print(bot.execute("Bana 3 tane banko maç ver"))
