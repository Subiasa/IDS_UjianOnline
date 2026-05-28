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
from core.sensors.window_tracker import WindowTracker
from core.sensors.clipboard_mon import ClipboardMonitor
from core.sensors.process_scanner import ProcessScanner
from network.api_client import ApiClient

def main():
    logger.info("=== HIDS Pemantau Ujian Online ===")
    logger.info("Versi: 1.0 (Desktop Agent)")
    
    api_client = ApiClient()
    
    # Tkinter Login GUI for Stealth Mode
    import tkinter as tk
    from tkinter import messagebox

    login_success = False

    def attempt_login(pin, user, pwd, window):
        nonlocal login_success
        window.config(cursor="watch")
        window.update()
        success, msg = api_client.login(pin, user, pwd)
        window.config(cursor="")
        if success:
            login_success = True
            window.destroy()
        else:
            messagebox.showerror("Login Gagal", msg)

    def on_closing():
        root.destroy()
        sys.exit(0)

    root = tk.Tk()
    root.title("Login HIDS Pemantau")
    root.geometry("300x300")
    root.resizable(False, False)
    root.protocol("WM_DELETE_WINDOW", on_closing)

    tk.Label(root, text="=== HIDS Pemantau Ujian ===", font=("Helvetica", 12, "bold")).pack(pady=15)

    tk.Label(root, text="PIN Sesi:").pack()
    entry_pin = tk.Entry(root)
    entry_pin.pack(pady=5)

    tk.Label(root, text="Username:").pack()
    entry_user = tk.Entry(root)
    entry_user.pack(pady=5)

    tk.Label(root, text="Password:").pack()
    entry_pass = tk.Entry(root, show="*")
    entry_pass.pack(pady=5)

    tk.Button(root, text="Login & Mulai Pemantauan", command=lambda: attempt_login(entry_pin.get(), entry_user.get(), entry_pass.get(), root), bg="#3b82f6", fg="white", font=("Helvetica", 10, "bold")).pack(pady=20)

    root.eval('tk::PlaceWindow . center')
    root.mainloop()

    if not login_success:
        logger.error("Login dibatalkan atau gagal.")
        sys.exit(1)
        
    logger.info("Login berhasil! Mengaktifkan sensor pemantauan...")
    
    # Buka koneksi WebSocket untuk siaran layar
    api_client.start_websocket()
    
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
