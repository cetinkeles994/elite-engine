import threading
import time
import webbrowser
import os
import sys
import subprocess
from app import app
from data_fetcher import run_elite_update

# --- LOGO & HEADER ---
LOGO = """
========================================
   KAHİN - GLOBAL ANALİZ MOTORU
   Versiyon: 5.0 (Oracle Edition)
========================================
"""

def start_browser():
    """Wait for server to start, then open browser."""
    time.sleep(3) # Give Flask a moment
    print("🌍 Tarayıcı açılıyor: http://127.0.0.1:5000")
    webbrowser.open("http://127.0.0.1:5000")

def run_flask():
    """Run Flask app."""
    # Turn off debug reloader for Thread safety
    app.run(debug=False, use_reloader=False, port=5000)

def run_data_loop():
    """Run data fetcher in a loop."""
    while True:
        print("\n⏳ Veri güncelleme döngüsü başladı...")
        try:
            run_elite_update()
            print("✅ Güncelleme tamamlandı. 60 saniye bekleme...")
        except Exception as e:
            print(f"❌ HATA: {e}")
        
        # Wait 60 seconds before next check
        time.sleep(60)

if __name__ == "__main__":
    # Force working directory to where the exe is (for PyInstaller)
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
        os.chdir(application_path)
        
        # --- FIRST RUN SETUP: extract default data if missing ---
        import shutil
        try:
            # PyInstaller temp folder
            bundle_dir = sys._MEIPASS
            
            for f_name in ["matches_cache.json", "history_cache.json"]:
                if not os.path.exists(f_name):
                    src = os.path.join(bundle_dir, f_name)
                    if os.path.exists(src):
                        print(f"📦 İlk kurulum: {f_name} kopyalanıyor...")
                        shutil.copy(src, f_name)
        except Exception as e:
            print(f"⚠️ Veri hazırlama uyarısı: {e}")

    print(LOGO)
    print("🚀 Sistem başlatılıyor...")

    # 1. Start Flask in Thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # 2. Start Data Fetcher in Thread
    data_thread = threading.Thread(target=run_data_loop, daemon=True)
    data_thread.start()

    # 3. Open Browser
    start_browser()

    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Sistem kapatılıyor...")
        sys.exit()
