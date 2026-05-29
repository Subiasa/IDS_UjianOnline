import os
import sys
import shutil
import subprocess

def main():
    print("=== Pembangunan Agen IDS Pemantau (Executable) ===")
    
    try:
        import PyInstaller
    except ImportError:
        print("MENGINSTAL PYINSTALLER...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    server_url = input("Masukkan URL Server Produksi (contoh: https://ujian.sekolah.edu) [Tekan Enter untuk lewati]: ").strip()
    
    config_path = os.path.join("src", "config.py")
    backup_path = os.path.join("src", "config.py.bak")
    
    if server_url:
        print(f"Mengonfigurasi agen untuk terhubung ke: {server_url}")
        # Backup config
        shutil.copyfile(config_path, backup_path)
        
        # Read and modify config
        with open(config_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        with open(config_path, "w", encoding="utf-8") as f:
            for line in lines:
                if line.startswith("SERVER_URL ="):
                    f.write(f'SERVER_URL = os.environ.get("SERVER_URL", "{server_url}")\n')
                else:
                    f.write(line)
                    
    try:
        print("MEMULAI PROSES BUILD...")
        # Compile using pyinstaller
        subprocess.check_call([
            "pyinstaller", 
            "--onefile", 
            "--noconsole", 
            "--name", "IDS_Pemantau_Agen",
            "--clean",
            os.path.join("src", "main.py")
        ])
        
        print("\n[SUKSES] Aplikasi berhasil dibangun!")
        print("Anda dapat menemukan file .exe di dalam folder 'dist'")
        
    finally:
        # Restore config if backed up
        if os.path.exists(backup_path):
            shutil.move(backup_path, config_path)
            print("Konfigurasi lokal dikembalikan.")

if __name__ == "__main__":
    main()
