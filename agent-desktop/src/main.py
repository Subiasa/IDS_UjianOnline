import os
import sys

# Ensure src is in sys.path so we can import without try-except blocks
src_path = os.path.dirname(os.path.abspath(__file__))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import threading
import time
import signal
from logger import logger
from core.window_tracker import WindowTracker
from core.clipboard_mon import ClipboardMonitor
from core.process_scanner import ProcessScanner
from network.api_client import ApiClient

def main():
    logger.info("=== HIDS Pemantau Ujian Online ===")
    logger.info("Versi: 1.0 (Desktop Agent)")
    
    api_client = ApiClient()
    
    # Simple CLI Login for Phase 1
    pin = input("Masukkan PIN Sesi: ")
    user = input("Masukkan Username: ")
    password = input("Masukkan Password: ")
    
    logger.info("Menghubungkan ke server...")
    success, msg = api_client.login(pin, user, password)
    
    if not success:
        logger.error(msg)
        sys.exit(1)
        
    logger.info("Login berhasil! Mengaktifkan sensor pemantauan...")
    
    # Define callback for sensors
    def on_anomaly(tipe, deskripsi):
        logger.warning(f"[ANOMALI TERDETEKSI] {tipe}: {deskripsi}")
        api_client.send_log_async(tipe, deskripsi)
        
    # Initialize sensors
    tracker = WindowTracker(on_anomaly)
    clip_mon = ClipboardMonitor(on_anomaly)
    proc_scan = ProcessScanner(on_anomaly)
    
    # Start sensors in separate threads
    threading.Thread(target=tracker.start, daemon=True).start()
    threading.Thread(target=clip_mon.start, daemon=True).start()
    threading.Thread(target=proc_scan.start, daemon=True).start()
    
    # Start heartbeat
    api_client.start_heartbeat()
    
    logger.info("Agen HIDS aktif. Jangan tutup jendela ini selama ujian berlangsung.")
    
    # Use Event for main thread graceful wait
    main_stop_event = threading.Event()
    
    def signal_handler(sig, frame):
        logger.info("\nMenerima sinyal terminasi. Mematikan agen...")
        tracker.stop()
        clip_mon.stop()
        proc_scan.stop()
        api_client.stop()
        main_stop_event.set()
        
    signal.signal(signal.SIGINT, signal_handler)
    
    # Wait until interrupted
    main_stop_event.wait()
    logger.info("Agen berhasil dimatikan dengan aman. Selesai.")

if __name__ == "__main__":
    main()
