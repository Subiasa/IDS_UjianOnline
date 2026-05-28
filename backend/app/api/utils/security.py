import hmac
import hashlib
import json
from datetime import datetime, timedelta
import jwt
from app.core.config import get_settings

settings = get_settings()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120 # 2 hours for exam

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_hmac_signature(payload_str: str, signature: str) -> bool:
    """Verifies HMAC-SHA256 signature from agent."""
    expected_mac = hmac.new(
        settings.AGENT_SECRET_KEY.encode(),
        payload_str.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_mac, signature)
