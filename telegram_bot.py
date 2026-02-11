import requests

# --- KAHİN TELEGRAM ALERTS (Phase 4) ---

# NOTE: Fill these with your actual bot token and chat ID
TOKEN = "7620251141:AAHG6F6F..." # Placeholder
CHAT_ID = "612345678" # Placeholder

def send_kahin_alert(message):
    """
    Sends a high-priority Oracle signal via Telegram.
    """
    if not TOKEN or "Placeholder" in TOKEN:
        # print("Telegram: No token provided.")
        return False
        
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.status_code == 200
    except Exception as e:
        print(f"Telegram Alert Error: {e}")
        return False

def format_match_alert(match):
    """
    Formats a match dictionary into a beautiful Telegram message.
    """
    home = match.get('home', 'Home')
    away = match.get('away', 'Away')
    league = match.get('league', 'League')
    score = match.get('score', '0-0')
    rec = match.get('pro_stats', {}).get('recommendation', 'Belli Değil')
    reason = match.get('pro_stats', {}).get('reasoning', '')
    conf = match.get('pro_stats', {}).get('confidence', 0)
    
    emoji = "🔮"
    if conf > 85: emoji = "🔥"
    
    text = f"{emoji} <b>KAHİN SİNYALİ ONAYLANDI!</b>\n\n"
    text += f"🏆 <b>Lig:</b> {league}\n"
    text += f"⚔️ <b>Maç:</b> {home} vs {away}\n"
    text += f"📊 <b>Skor:</b> {score}\n\n"
    text += f"💡 <b>Kahin Tahmini:</b> <u>{rec}</u> (Güven: %{conf})\n\n"
    if reason:
        text += f"📝 <b>Kahin Yorumu:</b> {reason}\n"
        
    text += f"\n<i>#Kahin #ValueBet #EliteEngine</i>"
    return text

if __name__ == "__main__":
    # Test alert
    # send_kahin_alert("🔮 KAHİN SISTEMI AKTIF!")
    pass
