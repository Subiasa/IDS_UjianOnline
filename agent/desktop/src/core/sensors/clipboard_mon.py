import pyperclip
import time
from typing import Callable
import threading

from logger import logger

class ClipboardMonitor:
    def __init__(self, callback: Callable[[str, str], None]):
        self.callback = callback
        self.stop_event = threading.Event()

    def start(self):
        logger.info("Memulai Clipboard Monitor...")
        last_clipboard = ""
        while not self.stop_event.is_set():
            try:
                current_content = pyperclip.paste()
                if current_content != last_clipboard:
                    if last_clipboard != "":  # Ignore first empty load
                        preview = current_content[:50] + "..." if len(current_content) > 50 else current_content
                        self.callback("CLIPBOARD_USAGE", f"Konten disalin/ditempel: {preview}")
                    last_clipboard = current_content
            except Exception as e:
                logger.error(f"Error pada ClipboardMonitor: {e}")
            
            time.sleep(1.5)

    def stop(self):
        logger.info("Menghentikan Clipboard Monitor...")
        self.stop_event.set()
