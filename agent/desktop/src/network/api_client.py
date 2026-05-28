import requests
import json
import hmac
import hashlib
import time
import threading
import queue

import config
from logger import logger

class ApiClient:
    def __init__(self):
        self.session = requests.Session()
        self.log_queue = queue.Queue()
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._queue_worker, daemon=True)
        self.worker_thread.start()

    def login(self, pin_sesi, username, password):
        payload = {
            "pin_sesi": pin_sesi,
            "username": username,
            "password": password
        }
        try:
            logger.info("Mencoba login agen...")
            response = self.session.post(f"{config.SERVER_URL}{config.API_PREFIX}/auth/agent-login", json=payload)
            if response.status_code == 200:
                data = response.json()
                config.SESSION_TOKEN = data["access_token"]
                config.PESERTA_ID = data["peserta_id"]
                logger.info("Login berhasil.")
                return True, "Login berhasil"
            else:
                logger.error(f"Login gagal: {response.text}")
                return False, f"Login gagal: {response.text}"
        except Exception as e:
            logger.error(f"Error koneksi saat login: {str(e)}")
            return False, f"Error koneksi: {str(e)}"

    def _generate_signature(self, raw_payload: str) -> str:
        return hmac.new(
            config.AGENT_SECRET_KEY.encode(),
            raw_payload.encode(),
            hashlib.sha256
        ).hexdigest()

    def _queue_worker(self):
        logger.debug("Background queue worker started.")
        while self.is_running:
            try:
                # Block for up to 1 second waiting for a log item
                log_item = self.log_queue.get(timeout=1)
                success = self._send_log_sync(log_item)
                if not success:
                    # If sending failed (e.g. offline), put it back in queue and wait before retrying
                    logger.warning("Gagal mengirim log, mengembalikan ke antrean (Offline Mode aktif).")
                    self.log_queue.put(log_item)
                    time.sleep(5) # Wait before retrying
                else:
                    self.log_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Kesalahan pada queue worker: {e}")
                time.sleep(1)

    def _send_log_sync(self, payload) -> bool:
        raw_payload = json.dumps(payload)
        signature = self._generate_signature(raw_payload)
        
        headers = {
            "X-Signature": signature,
            "Content-Type": "application/json"
        }
        
        try:
            response = self.session.post(
                f"{config.SERVER_URL}{config.API_PREFIX}/telemetry/log",
                data=raw_payload,
                headers=headers,
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Network error saat kirim log: {e}")
            return False

    def send_log_async(self, tipe_anomali, deskripsi):
        if not config.PESERTA_ID: 
            return
        
        payload = {
            "peserta_id": config.PESERTA_ID,
            "tipe_anomali": tipe_anomali,
            "metadata_log": {"deskripsi": deskripsi},
            "timestamp": time.time()
        }
        logger.info(f"Menambahkan log ke antrean: {tipe_anomali}")
        self.log_queue.put(payload)
        
        # Trigger tangkapan layar otomatis (event-triggered)
        threading.Thread(target=self.send_screenshot_sync, args=(True,), daemon=True).start()

    def send_screenshot_sync(self, is_anomaly=True):
        if not hasattr(self, 'ws_app') or not self.ws_app or not self.ws_app.sock:
            logger.warning("WebSocket tidak terhubung, gagal mengirim tangkapan layar.")
            return

        from core.sensors.screen_capture import capture_screen_webp
        base64_img = capture_screen_webp(quality=40)
        
        if base64_img:
            payload = {
                "type": "screenshot",
                "peserta_id": config.PESERTA_ID,
                "is_anomaly": is_anomaly,
                "image": base64_img,
                "timestamp": time.time()
            }
            # Tambahkan HMAC signature untuk keamanan
            raw_payload = json.dumps(payload, separators=(',', ':'))
            signature = self._generate_signature(raw_payload)
            payload["signature"] = signature
            
            try:
                self.ws_app.send(json.dumps(payload))
                logger.info("Tangkapan layar berhasil dikirim ke pengawas.")
            except Exception as e:
                logger.error(f"Gagal mengirim tangkapan layar: {e}")

    def start_websocket(self):
        try:
            import websocket
        except ImportError:
            logger.error("websocket-client belum diinstal. Harap jalankan 'pip install websocket-client'")
            return
            
        def on_message(ws, message):
            try:
                data = json.loads(message)
                if data.get("action") == "capture":
                    logger.info("Permintaan 'Intip Layar' diterima dari pengawas.")
                    threading.Thread(target=self.send_screenshot_sync, args=(False,), daemon=True).start()
                elif data.get("action") == "warning":
                    msg = data.get("message", "Perhatian!")
                    logger.warning(f"PESAN PERINGATAN DARI PENGAWAS: {msg}")
                    # Tampilkan pop-up peringatan
                    def show_warning():
                        import tkinter as tk
                        from tkinter import messagebox
                        # Buat root transparan yang akan hancur sendiri
                        root = tk.Tk()
                        root.withdraw()
                        root.attributes("-topmost", True)
                        messagebox.showwarning("Peringatan Pengawas", msg, parent=root)
                        root.destroy()
                    threading.Thread(target=show_warning, daemon=True).start()
            except Exception as e:
                logger.error(f"Error parsing WS message: {e}")

        def on_error(ws, error):
            logger.debug(f"WS error: {error}")

        def on_close(ws, close_status_code, close_msg):
            logger.info("Koneksi WS tertutup. Mencoba ulang dalam 10 detik...")
            # Avoid immediate recursion, use a separate thread or just let the main loop handle it
            if self.is_running:
                threading.Timer(10, self.start_websocket).start()

        def on_open(ws):
            logger.info("Berhasil terhubung ke WebSocket peladen untuk siaran langsung.")

        ws_url = config.SERVER_URL.replace("http://", "ws://").replace("https://", "wss://")
        url = f"{ws_url}{config.API_PREFIX.replace('/api/v1', '')}/ws/stream/{config.PESERTA_ID}"
        
        self.ws_app = websocket.WebSocketApp(url,
                                             on_open=on_open,
                                             on_message=on_message,
                                             on_error=on_error,
                                             on_close=on_close)
        
        threading.Thread(target=self.ws_app.run_forever, daemon=True).start()

    def start_heartbeat(self):
        def _beat():
            logger.debug("Heartbeat worker started.")
            while self.is_running:
                if config.PESERTA_ID:
                    payload = {
                        "peserta_id": config.PESERTA_ID,
                        "timestamp": time.time()
                    }
                    raw_payload = json.dumps(payload)
                    signature = self._generate_signature(raw_payload)
                    
                    headers = {
                        "X-Signature": signature,
                        "Content-Type": "application/json"
                    }
                    
                    try:
                        self.session.post(
                            f"{config.SERVER_URL}{config.API_PREFIX}/telemetry/heartbeat",
                            data=raw_payload,
                            headers=headers,
                            timeout=5
                        )
                    except Exception:
                        pass
                time.sleep(10) # Send heartbeat every 10 seconds

        threading.Thread(target=_beat, daemon=True).start()

    def stop(self):
        logger.info("Menghentikan modul network...")
        self.is_running = False
