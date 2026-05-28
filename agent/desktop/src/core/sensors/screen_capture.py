import mss
from PIL import Image
import io
import base64
from logger import logger

def capture_screen_webp(quality=40):
    try:
        with mss.mss() as sct:
            # Mengambil screenshot dari monitor utama
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)
            
            # Konversi ke gambar PIL
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            
            # Kompresi ke format WebP
            buffer = io.BytesIO()
            img.save(buffer, format="WEBP", quality=quality)
            
            # Konversi ke string Base64
            img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            return img_base64
    except Exception as e:
        logger.error(f"Gagal mengambil screenshot: {e}")
        return None
