import psutil
import time
import threading
from typing import Callable

from config import BLACKLISTED_PROCESSES
from logger import logger

class ProcessScanner:
    def __init__(self, callback: Callable[[str, str], None]):
        self.callback = callback
        self.stop_event = threading.Event()
        self.notified_processes = set()

    def start(self):
        logger.info("Memulai Process Scanner...")
        while not self.stop_event.is_set():
            try:
                for proc in psutil.process_iter(['name']):
                    try:
                        p_name = proc.info['name'].lower()
                        if p_name in BLACKLISTED_PROCESSES and p_name not in self.notified_processes:
                            logger.warning(f"Aplikasi terlarang terdeteksi: {p_name}")
                            self.callback("BLACKLISTED_PROCESS", f"Aplikasi terlarang berjalan: {p_name}")
                            self.notified_processes.add(p_name)
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
            except Exception as e:
                logger.error(f"Error pada ProcessScanner: {e}")
            
            # Use wait instead of sleep so it can be interrupted immediately
            self.stop_event.wait(5)

    def stop(self):
        logger.info("Menghentikan Process Scanner...")
        self.stop_event.set()
