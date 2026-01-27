import pandas as pd
from scipy.stats import poisson
import math
from data_fetcher import get_league_data

def calculate_kelly_stake(probability, odds, bankroll, fractional=0.25):
    """
    Calculates the detailed Kelly Criterion stake.
    """
    if probability <= 0 or probability >= 1:
        return {
            "is_value": False, 
            "stake_pct": 0, 
            "amount": 0, 
            "status": "Error: Prob must be between 0 and 1"
        }
    
    b = odds - 1
    p = probability
    q = 1 - p
    
    f_star = (b * p - q) / b
    
    if f_star > 0:
        safe_stake_pct = f_star * fractional
        MAX_STAKE_CAP = 0.05
        final_stake_pct = min(safe_stake_pct, MAX_STAKE_CAP)
        
        stake_amount = bankroll * final_stake_pct
        return {
            "is_value": True,
            "raw_kelly_pct": f_star * 100,
            "fractional_kelly_pct": safe_stake_pct * 100,
            "final_stake_pct": final_stake_pct * 100,
            "amount": stake_amount,
            "status": "BET"
        }
    else:
        return {
            "is_value": False,
            "raw_kelly_pct": 0,
            "fractional_kelly_pct": 0,
            "final_stake_pct": 0,
            "amount": 0,
            "status": "NO BET (No Edge)"
        }

def analyze_match(ev_sahibi, deplasman, ev_oran, beraberlik_oran, dep_oran, bankroll, stats_df, lig_avg):
    # --- 1. VERİ KONTROLÜ ---
    try:
        ev_stats = stats_df[stats_df['Takım'] == ev_sahibi].iloc[0]
        dep_stats = stats_df[stats_df['Takım'] == deplasman].iloc[0]
    except IndexError:
        return {"error": f"'{ev_sahibi}' veya '{deplasman}' veri tabanında bulunamadı."}

    # --- 2. GÜÇ HESAPLAMASI (xG) ---
    ev_attack_strength = ev_stats['Mac_Basi_Atilan_Ev'] / lig_avg
    dep_defense_weakness = dep_stats['Mac_Basi_Yenen_Dep'] / lig_avg
    ev_xg = ev_attack_strength * dep_defense_weakness * lig_avg
    
    dep_attack_strength = dep_stats['Mac_Basi_Atilan_Dep'] / lig_avg
    ev_defense_weakness = ev_stats['Mac_Basi_Yenen_Ev'] / lig_avg
    dep_xg = dep_attack_strength * ev_defense_weakness * lig_avg

    # Ev Sahibi Avantajı (%10)
    ev_xg *= 1.10

    # --- 3. POISSON ---
    ev_ihtimal_list = [poisson.pmf(i, ev_xg) for i in range(10)]
    dep_ihtimal_list = [poisson.pmf(i, dep_xg) for i in range(10)]

    ms1_prob, draw_prob, ms2_prob = 0, 0, 0
    for i in range(10):
        for j in range(10):
            olasilik = ev_ihtimal_list[i] * dep_ihtimal_list[j]
            if i > j: ms1_prob += olasilik
            elif i == j: draw_prob += olasilik
            else: ms2_prob += olasilik

    adil_oran_ms1 = 1 / ms1_prob if ms1_prob > 0 else 0
    adil_oran_ms0 = 1 / draw_prob if draw_prob > 0 else 0
    adil_oran_ms2 = 1 / ms2_prob if ms2_prob > 0 else 0

    # --- 4. KARAR ---
    bets = []
    bahisler = [
        ("MS1", "Ev Sahibi", ms1_prob, ev_oran, adil_oran_ms1),
        ("MS0", "Beraberlik", draw_prob, beraberlik_oran, adil_oran_ms0),
        ("MS2", "Deplasman", ms2_prob, dep_oran, adil_oran_ms2)
    ]
    
    for code, isim, olasilik, buro_orani, gercek_oran in bahisler:
        sonuc = calculate_kelly_stake(olasilik, buro_orani, bankroll)
        bets.append({
            "code": code,
            "name": isim,
            "prob": round(olasilik * 100, 1),
            "fair_odds": round(gercek_oran, 2),
            "bookie_odds": buro_orani,
            "is_value": sonuc["is_value"],
            "stake_pct": round(sonuc["final_stake_pct"] * 100, 2),
            "stake_amount": round(sonuc["amount"], 2),
            "status": sonuc["status"],
            "expected_value": round((olasilik * buro_orani) - 1, 3) 
        })

    return {
        "match_info": {
            "home": ev_sahibi,
            "away": deplasman,
            "home_xg": round(ev_xg, 2),
            "away_xg": round(dep_xg, 2),
            "home_form": round(ev_stats['Mac_Basi_Atilan_Ev'], 2),
            "away_form": round(dep_stats['Mac_Basi_Yenen_Dep'], 2)
        },
        "bets": bets
    }

# --- ANA AKIŞ ---
if __name__ == "__main__":
    print("\n--- BET SİSTEMİ BAŞLATILIYOR (V2.0 - GERÇEK VERİ) ---")
    
    # 1. Verileri İndir
    df_stats, lig_avg, home_avg, away_avg = get_league_data(season='2425', league='T1')
    
    if df_stats is None:
        print("Veri çekilemedi, işlem iptal.")
        exit()

    # --- INTERAKTİF MOD ---
    print("\n" + "="*50)
    print("SİSTEM HAZIR! (Çıkmak için 'q' yazıp Enter'a basın)")
    print("Takım isimlerini Türkçe karakter kullanmadan yazın.")
    print("Mevcut Takımlar (Örnek): Fenerbahce, Galatasaray, Besiktas, Trabzonspor, Samsunspor...")
    print("="*50)

    kasa = 10000 # Başlangıç Kasası

    while True:
        print("\n--- YENİ ANALİZ ---")
        ev = input("Ev Sahibi Takım: ").strip()
        if ev.lower() == 'q': break
        
        dep = input("Deplasman Takım: ").strip()
        if dep.lower() == 'q': break
        
        try:
            oran1 = float(input("MS1 Oranı (Ev): "))
            oran0 = float(input("MS0 Oranı (Beraberlik): "))
            oran2 = float(input("MS2 Oranı (Deplasman): "))
        except ValueError:
            print("Hata: Lütfen oranları sayı olarak girin (Örn: 1.50).")
            continue

        result = analyze_match(ev, dep, oran1, oran0, oran2, kasa, df_stats, lig_avg)
        
        if "error" in result:
            print(result["error"])
            continue

        print(f"\nMAÇ: {result['match_info']['home']} vs {result['match_info']['away']}")
        print(f"xG: {result['match_info']['home_xg']} - {result['match_info']['away_xg']}")
        
        print("-" * 60)
        for bet in result['bets']:
           isaret = ">>> " if bet["is_value"] else "    "
           print(f"{isaret}{bet['name']:<15} | {bet['prob']:>5}% | Oran: {bet['bookie_odds']:<4} | {bet['status']} ({bet['stake_amount']} TL)")
