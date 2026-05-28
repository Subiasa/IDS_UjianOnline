import hmac
import hashlib
import json
import time
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from app.core.config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120 # 2 hours for exam

def get_password_hash(password: str) -> str:
    # Bcrypt has a 72-byte limit. We truncate to ensure passlib doesn't raise ValueError.
    return pwd_context.hash(password[:72])

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password[:72], hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_hmac_signature(payload_str: str, signature: str, timestamp: float = None) -> bool:
    """Verifies HMAC-SHA256 signature from agent and checks timestamp for replay attacks."""
    # 1. Check timestamp (allow +/- 60 seconds)
    if timestamp:
        current_time = time.time()
        if abs(current_time - timestamp) > 60:
            return False

    # 2. Verify Signature
    expected_mac = hmac.new(
        settings.AGENT_SECRET_KEY.encode(),
        payload_str.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_mac, signature)
