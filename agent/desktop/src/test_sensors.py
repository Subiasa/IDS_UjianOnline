import threading
import time
import signal

try:
    from logger import logger
    from core.sensors.window_tracker import WindowTracker
    from core.sensors.clipboard_mon import ClipboardMonitor
    from core.sensors.process_scanner import ProcessScanner
except ImportError:
    from src.logger import logger
    from src.core.sensors.window_tracker import WindowTracker
    from src.core.sensors.clipboard_mon import ClipboardMonitor
    from src.core.sensors.process_scanner import ProcessScanner

def main():
    logger.info("=== MODE UJI COBA SENSOR (OFFLINE) ===")
    logger.info("Server tidak terhubung. Semua log hanya akan dicetak di layar.")
    logger.info("-" * 50)
    
    def on_anomaly(tipe, deskripsi):
        logger.warning(f"[ANOMALI] {tipe}")
        logger.warning(f"Detail: {deskripsi}")
        
    tracker = WindowTracker(on_anomaly)
    clip_mon = ClipboardMonitor(on_anomaly)
    proc_scan = ProcessScanner(on_anomaly)
    
    threading.Thread(target=tracker.start, daemon=True).start()
    threading.Thread(target=clip_mon.start, daemon=True).start()
    threading.Thread(target=proc_scan.start, daemon=True).start()
    
    logger.info("Sensor telah aktif! Coba lakukan:")
    logger.info("1. Pindah ke aplikasi lain (Window Tracking)")
    logger.info("2. Copy-paste sebuah teks (Clipboard Monitor)")
    logger.info("3. Buka Discord atau WhatsApp (Process Scanner)")
    logger.info("Tekan Ctrl+C untuk berhenti.")
    
    main_stop_event = threading.Event()
    
    def signal_handler(sig, frame):
        logger.info("\nMematikan sensor...")
        tracker.stop()
        clip_mon.stop()
        proc_scan.stop()
        main_stop_event.set()
        
    signal.signal(signal.SIGINT, signal_handler)
    
    main_stop_event.wait()
    logger.info("Selesai.")

if __name__ == "__main__":
    main()
