import pandas as pd
import io
import requests
import os

def get_league_data(season='2425', league='T1'):
    """
    Fetches league data from local file or football-data.co.uk
    """
    url = f"https://www.football-data.co.uk/mmz4281/{season}/{league}.csv"
    local_file = f"{league}.csv"
    df_raw = None

    # 1. Try Local File
    if os.path.exists(local_file):
        print(f"Bilgi: Yerel dosya kullanılıyor -> {local_file}")
        try:
            df_raw = pd.read_csv(local_file)
            if 'HomeTeam' not in df_raw.columns:
                print("Yerel dosya formatı hatalı, indirme denenecek.")
                df_raw = None
        except Exception as e:
            print(f"Yerel dosya okunamadı: {e}")

    # 2. Try Download (if no local data)
    if df_raw is None:
        print(f"Veri indiriliyor: {url}...")
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Bağlantı denemesi {attempt+1}/{max_retries}...")
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                df_raw = pd.read_csv(io.StringIO(response.text))
                break 
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"Bağlantı hatası: {e}")
                else:
                    print(f"Hata: {e}. Tekrar deneniyor...")
                    import time
                    time.sleep(2)

    # 3. Process Data
    if df_raw is None:
        print("HATA: Veri kaynaktan çekilemedi.")
        return None, None, None, None

    try:
        # Filter only finished matches
        if 'FTHG' not in df_raw.columns: 
             # Maybe the mock CSV didn't strictly follow structure or empty
             print("Uyarı: Gol verisi bulunamadı.")
             return None, None, None, None
             
        df_played = df_raw.dropna(subset=['FTHG', 'FTAG'])
        
        if df_played.empty:
            print("Uyarı: Oynanmış maç bulunamadı.")
            return None, 1.0, 1.0, 1.0 

        total_home_goals = df_played['FTHG'].sum()
        total_away_goals = df_played['FTAG'].sum()
        total_matches = len(df_played)
        
        avg_home_goals_league = total_home_goals / total_matches
        avg_away_goals_league = total_away_goals / total_matches
        league_avg_goals = (avg_home_goals_league + avg_away_goals_league)
        
        print(f"Analiz edilen maç sayısı: {total_matches}")
        
        teams = pd.unique(df_played[['HomeTeam', 'AwayTeam']].values.ravel('K'))
        stats = []

        for team in teams:
            home_games = df_played[df_played['HomeTeam'] == team]
            played_home = len(home_games)
            scored_home = home_games['FTHG'].sum()
            conceded_home = home_games['FTAG'].sum()
            
            away_games = df_played[df_played['AwayTeam'] == team]
            played_away = len(away_games)
            scored_away = away_games['FTAG'].sum()
            conceded_away = away_games['FTHG'].sum()
            
            avg_scored_home = scored_home / played_home if played_home > 0 else 0
            avg_conceded_home = conceded_home / played_home if played_home > 0 else 0
            
            avg_scored_away = scored_away / played_away if played_away > 0 else 0
            avg_conceded_away = conceded_away / played_away if played_away > 0 else 0
            
            stats.append({
                'Takım': team,
                'Mac_Basi_Atilan_Ev': avg_scored_home,
                'Mac_Basi_Yenen_Ev': avg_conceded_home,
                'Mac_Basi_Atilan_Dep': avg_scored_away,
                'Mac_Basi_Yenen_Dep': avg_conceded_away,
                'Toplam_Mac': played_home + played_away
            })
            
        df_stats = pd.DataFrame(stats)
        return df_stats, league_avg_goals, avg_home_goals_league, avg_away_goals_league

    except Exception as e:
        print(f"Veri işleme hatası: {e}")
        return None, None, None, None

if __name__ == "__main__":
    df, avg, h, a = get_league_data()
    if df is not None:
        print(df.head())
