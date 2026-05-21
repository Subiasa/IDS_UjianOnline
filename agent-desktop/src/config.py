SERVER_URL = "http://127.0.0.1:8000"
API_PREFIX = "/api/v1"
AGENT_SECRET_KEY = "kunci_rahasia_hmac_untuk_agen_desktop_dan_mobile" # Should match server config

# Will be set dynamically after login
SESSION_TOKEN = None
PESERTA_ID = None

BLACKLISTED_PROCESSES = [
    "discord.exe",
    "whatsapp.exe",
    "telegram.exe",
    "skype.exe",
    "teamviewer.exe",
    "anydesk.exe"
]
