import subprocess
import time
import sys
import os

def run_launcher():
    """
    KAHİN Launcher'ın sürekli çalışmasını sağlayan koruyucu script.
    Eğer hata alırsa veya kapanırsa 5 saniye içinde otomatik yeniden başlatır.
    """
    # Mevcut dizini launcher'ın olduğu yer olarak sabitle
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("🛡️  KAHİN Keep-Alive Sistemi Başlatıldı.")
    print("🚀 Launcher izleniyor...")

    while True:
        try:
            # Launcher'ı ayrı bir process olarak başlat
            # stdout ve stderr'i konsola aktar
            process = subprocess.Popen([sys.executable, "launcher.py"])
            
            # Process bitene kadar bekle
            process.wait()
            
            if process.returncode != 0:
                print(f"⚠️  Launcher hata ile kapandı (Kod: {process.returncode}). Yeniden başlatılıyor...")
            else:
                print("ℹ️  Launcher normal şekilde kapandı. Kural gereği yeniden başlatılıyor...")
                
        except Exception as e:
            print(f"❌ Beklenmedik Hata: {e}")
            
        time.sleep(5) # 5 saniye bekle ve tekrar dene

if __name__ == "__main__":
    run_launcher()
