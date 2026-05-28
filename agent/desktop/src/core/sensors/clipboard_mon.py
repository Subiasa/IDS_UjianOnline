import pyperclip
import time
from typing import Callable
import threading

from logger import logger

class ClipboardMonitor:
    def __init__(self, callback: Callable[[str, str], None]):
        self.callback = callback
        self.stop_event = threading.Event()
        self.last_report_time = 0
        self.report_cooldown = 2 # Detik

    def start(self):
        logger.info("Memulai Clipboard Monitor...")
        last_clipboard = ""
        while not self.stop_event.is_set():
            try:
                current_content = pyperclip.paste()
                if current_content != last_clipboard:
                    current_time = time.time()
                    # Filter: Hanya lapor jika teks cukup panjang (>3 karakter) dan bukan pengulangan cepat
                    if last_clipboard != "" and len(current_content.strip()) > 3:
                        if current_time - self.last_report_time > self.report_cooldown:
                            preview = current_content[:50] + "..." if len(current_content) > 50 else current_content
                            self.callback("CLIPBOARD_USAGE", f"Konten disalin/ditempel: {preview}")
                            self.last_report_time = current_time
                    
                    last_clipboard = current_content
            except Exception as e:
                logger.error(f"Error pada ClipboardMonitor: {e}")
            
            self.stop_event.wait(1.5)

    def stop(self):
        logger.info("Menghentikan Clipboard Monitor...")
        self.stop_event.set()
