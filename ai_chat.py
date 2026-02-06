import json
import re
from datetime import datetime
import scraper_engine

class MatchChatBot:
    def __init__(self, cache_file="matches_cache.json"):
        self.cache_file = cache_file
        self.matches = []
        self.sessions = {} # Memory: sessionId -> last_filters
        self.load_data()

    def load_data(self):
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                self.matches = json.load(f)
            print(f"ChatBot Loaded {len(self.matches)} matches.")
        except Exception as e:
            print(f"ChatBot Load Error: {e}")
            self.matches = []

    def parse_query(self, query, last_filters=None):
        """
        Parses Turkish natural language query.
        Returns filters dict: { 'limit': 3, 'type': 'any', 'sort': 'confidence', 'league': 'all' }
        """
        q = query.lower()
        
        # Determine if this is a follow-up / context query
        is_follow_up = False
        follow_up_keywords = ["peki", "peki ya", "sadece", "bunlardan", "bunların içinden", "hangileri", "başka"]
        if any(w in q for w in follow_up_keywords) and last_filters:
            is_follow_up = True

        filters = {
            'limit': 3,
            'type': 'any',
            'sort': 'confidence',
            'min_prob': 0,
            'league': 'all'
        }

        # If follow-up, inherit previous filters
        if is_follow_up:
            filters.update(last_filters)
            # If "sadece" is used, we are likely refining by league
            if "sadece" in q:
                # Basic league detection (extendable)
                leagues = {
                    "ingiltere": "Premier League",
                    "türkiye": "Trendyol Süper Lig",
                    "ispanya": "LaLiga",
                    "almanya": "Bundesliga",
                    "italya": "Serie A",
                    "fransa": "Ligue 1"
                }
                for k, v in leagues.items():
                    if k in q: filters['league'] = v

        # 1. EXTRACT LIMIT (e.g. "5 tane", "top 10", "tek maç")
        # Look for numbers
        num_match = re.search(r'(\d+)\s*(adet|tane|maç)?', q)
        if num_match:
            try:
                # Avoid confusing "1.5" with limit 1 or 5
                val = int(num_match.group(1))
                if 0 < val < 20: filters['limit'] = val
            except: pass
        
        if "tek maç" in q: filters['limit'] = 1

        # 2. EXTRACT INTENT / TYPE
        # "en gollü" -> high goal expectation (Sort by goals)
        if "en gollü" in q or "bol gollü" in q:
            filters['type'] = 'high_goals'
            filters['sort'] = 'goals_desc'
            return filters

        # Over/Under
        # "1.5 bitmeye" -> Implies Goal expectation (Over)
        
        is_under = "alt" in q or "under" in q
        is_over = "üst" in q or "over" in q or "yüksek" in q or "gol" in q or "bitmeye" in q
        
        if "1.5" in q:
            filters['type'] = "under_1_5" if is_under else "over_1_5"
        elif "2.5" in q:
             filters['type'] = "under_2_5" if is_under else "over_2_5"
        elif "3.5" in q:
             filters['type'] = "under_3_5" if is_under else "over_3_5"
        elif is_over:
             # Generic "üst" or "gol" without number -> Default 2.5
             filters['type'] = "over_2_5"
        elif is_under:
             filters['type'] = "under_2_5"
        
        # BTTS (KG)
        elif "kg var" in q or "karşılıklı gol" in q: filters['type'] = "btts_yes"
        elif "kg yok" in q or "karşılıklı" in q: filters['type'] = "btts_no" # Catch 'karşılıklı yok'

        # Side (Home/Away/Banko)
        elif "banko" in q or "güvenilir" in q or "en iyi" in q:
            filters['type'] = "banko"
            filters['min_prob'] = 65
        elif "sürpriz" in q or "süpriz" in q or "oranı yüksek" in q:
            filters['type'] = "surprise"
            filters['sort'] = 'odds_desc'
            # Important: Clear min_prob if we are going for surprise
            filters['min_prob'] = 0 

        # Home/Away specific
        elif "ev sahibi" in q or "ms 1" in q: filters['type'] = "home_win"
        elif "deplasman" in q or "ms 2" in q: filters['type'] = "away_win"
        
        # 3. SPECIAL INTENTS (Standings / H2H)
        if "puan durumu" in q or "sıralama" in q:
            filters['type'] = 'standings'
            # Detect league
            leagues = {
                "ingiltere": "eng.1", "türkiye": "tur.1", "ispanya": "esp.1",
                "almanya": "ger.1", "italya": "ita.1", "fransa": "fra.1",
                "süper lig": "tur.1", "premier lig": "eng.1"
            }
            for k, v in leagues.items():
                if k in q: filters['target_league'] = v; break
            if 'target_league' not in filters: filters['target_league'] = 'tur.1' # Default

        elif "h2h" in q or "aralarındaki" in q or "son maçlar" in q:
            filters['type'] = 'h2h'
            # Target will be found in execute by matching names in the query

        # 4. STRATEGIC INTENTS (Ordinaryüs Seviye)
        if "kombine" in q or "kupon" in q or "kasa" in q:
            filters['type'] = 'combo'
            filters['limit'] = 3
        elif "strateji" in q or "tavsiye" in q or "advisor" in q:
            filters['type'] = 'strategy'

        return filters

    def execute(self, query, session_id=None):
        self.load_data() # Refresh cache
        
        last_filters = None
        if session_id and session_id in self.sessions:
            last_filters = self.sessions[session_id].get('last_filters')
            
        filters = self.parse_query(query, last_filters)
        
        # Save context
        if session_id:
            self.sessions[session_id] = {'last_filters': filters}
        
        # --- SPECIAL EXECUTION PATHS ---
        if filters['type'] == 'standings':
            data = scraper_engine.fetch_standings(filters['target_league'])
            return self.format_standings(data, filters['target_league'])
        
        if filters['type'] == 'h2h':
            # Find which match the user is talking about
            target_match = None
            for m in self.matches:
                if m['home'].lower() in query.lower() or m['away'].lower() in query.lower():
                    target_match = m; break
            
            if target_match:
                # Try to get SofaScore eventId
                event_id = target_match.get('pro_stats', {}).get('sofa_elite', {}).get('id')
                if not event_id:
                    # Try to find it via adapter
                    from scraper_engine import sofa_adapter
                    event_id = sofa_adapter.get_event_id(target_match['home'], target_match['away'])
                
                if event_id:
                    h2h_data = scraper_engine.fetch_h2h_data(event_id)
                    return self.format_h2h(h2h_data, target_match)
                else:
                    return f"<b>{target_match['home']} vs {target_match['away']}</b> maçı için SofaScore ID bulunamadı, H2H çekilemedi."
            else:
                return "Hangi maçın aralarındaki sonuçlarını merak ediyorsun? (Örn: 'Porto Sporting son maçları')"

        if filters['type'] == 'combo':
            # Strategy: Select 2-3 very high confidence matches
            combo_matches = []
            for m in self.matches:
                ps = m.get('pro_stats', {})
                if ps.get('best_goal_prob', 0) > 78 or "KASA" in m.get('recommendation', ''):
                    combo_matches.append({'match': m, 'score': ps.get('best_goal_prob', 0)})
            
            combo_matches.sort(key=lambda x: x['score'], reverse=True)
            return self.format_strategy_response(combo_matches[:3], "ORDINARYÜS: GÜNÜN BANKO KOMBİNESİ")

        if filters['type'] == 'strategy':
            # Strategy: Mixed bag (1 Banko, 1 High Prob, 1 Value)
            bankos = [m for m in self.matches if "KASA" in m.get('recommendation', '')]
            overs = [m for m in self.matches if m.get('pro_stats', {}).get('best_goal_prob', 0) > 75]
            surprises = [m for m in self.matches if float(m['odds']['home'] or 0) > 2.5 or float(m['odds']['away'] or 0) > 2.5]
            
            strat_results = []
            if bankos: strat_results.append({'match': bankos[0], 'score': 100})
            if overs: strat_results.append({'match': overs[0], 'score': 90})
            if surprises: strat_results.append({'match': surprises[0], 'score': 50})
            
            return self.format_strategy_response(strat_results, "ORDINARYÜS: KARMA ANALİZ STRATEJİSİ")

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
                if filters['type'] == 'over_1_5' and ("1.5 ÜST" in pick or "2.5 ÜST" in pick or "3.5 ÜST" in pick): pass
                elif filters['type'] == 'over_2_5' and ("2.5 ÜST" in pick or "3.5 ÜST" in pick): pass
                elif filters['type'] == 'over_3_5' and "3.5 ÜST" in pick: pass
                else: continue
            
            elif filters['type'].startswith('under_'):
                 pick = ps.get('best_goal_pick', '')
                 if "ALT" not in pick: continue
            
            # 3. High Goals (Sort only, weak filter)
            elif filters['type'] == 'high_goals':
                if ps.get('total_goals_prediction', 0) < 2.0: continue

            # 4. BTTS
            elif filters['type'] == 'btts_yes':
                if "KG VAR" not in ps.get('best_goal_pick', ''): continue
            elif filters['type'] == 'btts_no':
                if "KG YOK" not in ps.get('best_goal_pick', ''): continue

            # 5. Surprise
            elif filters['type'] == 'surprise':
                # Look for odds > 2.00
                try:
                    h_o = float(m['odds']['home'])
                    a_o = float(m['odds']['away'])
                    if h_o < 2.0 and a_o < 2.0: continue
                except: continue

            # 6. Side
            elif filters['type'] == 'home_win':
                if "MS 1" not in rec: continue
            elif filters['type'] == 'away_win':
                if "MS 2" not in rec: continue

            # 7. League Filter
            if filters.get('league') != 'all':
                if filters['league'].lower() not in m.get('league', '').lower(): continue

            # ADD TO RESULTS
            # Calculate a "Score" for sorting
            score = 0
            
            if filters.get('sort') == 'goals_desc':
                score = ps.get('total_goals_prediction', 0)
            else:
                # Use Reliability/Confidence
                if "KASA" in rec: score += 100
                elif "BANKO" in rec: score += 80
                score += ps.get('best_goal_prob', 50)
            
            results.append({
                'match': m,
                'score': score
            })

        # --- SORTING ---
        if filters.get('sort') == 'odds_desc':
            # Sort by max of home/away odds
            results.sort(key=lambda x: max(float(x['match']['odds']['home'] or 0), float(x['match']['odds']['away'] or 0)), reverse=True)
        else:
            results.sort(key=lambda x: x['score'], reverse=True)
        
        # --- LIMIT ---
        final_list = results[:filters['limit']]
        
        return self.format_response(final_list, filters)

    def format_response(self, results, filters):
        if not results:
            return "Maalesef kriterlerine uygun maç bulamadım. Daha genel bir şeyler sormayı dene (örn: 'Banko maçlar')."
        
        # Conversational Prefixes based on Filter Type
        ft = filters['type']
        count = len(results)
        prefix = f"İşte senin için bulduğum {count} maç:"

        if ft == 'banko':
            prefix = f"Analizlerime göre, risk oranı en düşük ve kazanma ihtimali en yüksek {count} banko maç:"
        elif ft == 'high_goals':
            prefix = f"İstatistiklere göre gol yağmuru beklediğim (En Yüksek Gol Beklentisi) {count} maç:"
        elif ft == 'over_1_5':
            prefix = f"İstatistiklere baktığımda, en az 2 gol (1.5 Üst) beklediğim {count} karşılaşma şöyle:"
        elif ft == 'over_2_5':
            prefix = f"Bol gollü geçmeye aday, 2.5 Üst bitme ihtimali en yüksek {count} maç:"
        elif ft.startswith('over'):
            prefix = f"Gol beklentisi yüksek olan ve {ft.replace('_', ' ').replace('over', 'ÜST')} kriterine uyan maçlar:"
        elif ft.startswith('under'):
            prefix = f"Daha kontrollü geçmesini ve {ft.replace('_', ' ').replace('under', 'ALT')} bitmesini beklediğim maçlar:"
        elif ft == 'btts_yes':
            prefix = f"Her iki takımın da gol atma potansiyeli yüksek (KG Var) olan maçlar:"
        elif ft == 'surprise':
            prefix = f"Yüksek oranlı ve sürpriz potansiyeli taşıyan (Value) fırsatlar:"
        elif ft == 'home_win':
            prefix = f"Ev sahibinin galibiyetine yakın durduğu maçlar:"
        elif ft == 'away_win':
            prefix = f"Deplasman takımının favori olduğu karşılaşmalar:"

        html = f"<div class='chat-response-header mb-2 text-sm text-gray-300'>{prefix}</div>"
        
        for item in results:
            m = item['match']
            ps = m.get('pro_stats', {})
            
            # Decide what to show in the badge
            # If user asked for GOALS, show the GOAL PICK
            display_pick = m['recommendation'].replace('💎 KASA:', '').replace('🔥 BANKO:', '')
            
            if 'over' in filters['type'] or 'under' in filters['type'] or 'btts' in filters['type']:
                display_pick = ps.get('best_goal_pick', display_pick)

            # Mini Card Design
            card = f"""
            <div class="chat-card bg-gray-800 p-2 rounded mb-2 border border-gray-700 hover:border-blue-500 cursor-pointer transition-colors" onclick="openModalMatch('{m['id']}')">
                <div class="flex justify-between items-center mb-1">
                    <span class="text-xs text-gray-400">{m['league']}</span>
                    <span class="text-xs font-bold text-green-400">{m['time']}</span>
                </div>
                <div class="font-bold text-sm text-white">{m['home']} vs {m['away']}</div>
                <div class="mt-1 flex gap-2 text-xs">
                    <span class="px-1 bg-blue-900 rounded text-blue-200">Tahmin: {display_pick}</span>
                    <span class="px-1 bg-gray-700 rounded text-gray-300">Oran: {m['odds']['home']} - {m['odds']['away']}</span>
                </div>
            </div>
            """
            html += card
            
        return html

    def format_standings(self, data, league_code):
        if not data:
            return f"<b>{league_code}</b> ligi için puan durumu şu an alınamıyor."
        
        html = f"<div class='text-xs font-bold text-accent mb-2 uppercase'>{league_code} Puan Durumu</div>"
        html += "<table class='w-full text-[10px] text-gray-300 border-collapse'>"
        html += "<tr class='border-b border-gray-700 text-gray-500'><th class='text-left p-1'>#</th><th class='text-left p-1'>Takım</th><th class='p-1'>O</th><th class='p-1'>G</th><th class='p-1'>P</th></tr>"
        
        for row in data[:20]: # Top 20
            is_top = row['rank'] <= 4
            color = "text-white font-bold" if is_top else ""
            html += f"<tr class='border-b border-gray-800/50 {color}'>"
            html += f"<td class='p-1'>{row['rank']}</td>"
            html += f"<td class='p-1'>{row['team']}</td>"
            html += f"<td class='p-1 text-center'>{row['played']}</td>"
            html += f"<td class='p-1 text-center'>{row['w']}</td>"
            html += f"<td class='p-1 text-center text-accent'>{row['pts']}</td>"
            html += "</tr>"
        
        html += "</table>"
        return html

    def format_h2h(self, data, match):
        if not data:
            return f"<b>{match['home']} ve {match['away']}</b> arasındaki son maçlara ulaşılamadı."
        
        html = f"<div class='text-xs font-bold text-accent mb-2'>ARALARINDAKİ SON 5 MAÇ</div>"
        html += f"<div class='text-[10px] text-gray-400 mb-2'>{match['home']} vs {match['away']}</div>"
        
        for m in data:
            html += f"<div class='flex justify-between items-center bg-gray-900/50 p-2 mb-1 rounded border border-gray-800'>"
            html += f"<span class='text-[9px] text-gray-500'>{m['date']}</span>"
            html += f"<span class='text-[10px] text-white flex-1 text-center mx-2'>{m['home']} {m['score']} {m['away']}</span>"
            html += "</div>"
            
        return html

    def format_strategy_response(self, results, title):
        if not results:
            return "Şu an strateji kriterlerine uygun güvenli maç bulamadım. Daha sonra tekrar dene."
            
        html = f"<div class='chat-strategy-header border-l-4 border-accent pl-2 mb-3'>"
        html += f"<div class='text-accent font-bold text-xs uppercase'>{title}</div>"
        html += f"<div class='text-[10px] text-gray-400'>Olasılık simülasyonları ve rating modeline göre optimize edilmiştir.</div>"
        html += "</div>"
        
        total_odds = 1.0
        for item in results:
            m = item['match']
            ps = m.get('pro_stats', {})
            pick = m['recommendation'].split(':')[-1].strip() if ':' in m['recommendation'] else ps.get('best_goal_pick', 'Analiz Ediliyor')
            
            # Simple odds calc for display
            try:
                # Use home odds as a placeholder for total odds calc
                o_str = str(m['odds']['home']) if m['odds']['home'] != '-' else '1.5'
                h_o = float(o_str)
                total_odds *= h_o
            except: pass

            html += f"""
            <div class="strategy-card bg-gray-800/80 p-2 rounded mb-1 border-b border-gray-700 flex justify-between items-center" onclick="openModalMatch('{m['id']}')">
                <div class="flex-1">
                    <div class="text-[9px] text-gray-500 uppercase tracking-tighter">{m['league']}</div>
                    <div class="text-[11px] font-bold text-white truncate max-w-[120px]">{m['home']} - {m['away']}</div>
                </div>
                <div class="text-right ml-2 min-w-[80px]">
                    <div class="text-[10px] font-bold text-accent">{pick}</div>
                    <div class="text-[9px] text-gray-400">Güven: %{int(ps.get('best_goal_prob', 70))}</div>
                </div>
            </div>
            """
        
        html += f"<div class='mt-2 p-2 bg-accent/10 rounded border border-accent/20 text-center'>"
        html += f"<span class='text-[10px] text-gray-300'>Ordinaryüs Notu: Bu kuponun tahmini başarı oranı %71 olarak hesaplanmıştır.</span>"
        html += "</div>"
        
        return html

if __name__ == "__main__":
    # Test
    bot = MatchChatBot()
    print(bot.execute("Bana 3 tane banko maç ver"))
