import pygetwindow as gw
import time
from typing import Callable
import threading

from logger import logger

class WindowTracker:
    def __init__(self, callback: Callable[[str, str], None]):
        self.callback = callback
        self.stop_event = threading.Event()
        self.last_active_window = ""

    def start(self):
        logger.info("Memulai Window Tracker...")
        while not self.stop_event.is_set():
            try:
                active_window = gw.getActiveWindow()
                if active_window is not None:
                    current_title = active_window.title
                    if current_title != self.last_active_window and current_title != "":
                        self.callback("WINDOW_SWITCHING", f"Beralih ke jendela: {current_title}")
                        self.last_active_window = current_title
            except Exception as e:
                logger.error(f"Error pada WindowTracker: {e}")
            
            # Use wait for interruptible sleep
            self.stop_event.wait(1)

    def stop(self):
        logger.info("Menghentikan Window Tracker...")
        self.stop_event.set()
