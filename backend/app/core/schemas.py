from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class CredentialCreateRequest(BaseModel):
    username: str
    password: str
    pin_sesi: str

class BulkCredentialCreateRequest(BaseModel):
    pin_sesi: str
    count: int = 5
    password_default: str = "ujian123"

class CredentialCreateResponse(BaseModel):
    message: str
    username: str
    pin_sesi: str

class AgentLoginRequest(BaseModel):
    pin_sesi: str
    username: str
    password: str

class AgentLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    peserta_id: int

class Heartbeat(BaseModel):
    peserta_id: int
    timestamp: float

class LogAnomaliCreate(BaseModel):
    peserta_id: int
    tipe_anomali: str
    metadata_log: Dict[str, Any]
    timestamp: float

class TelemetryPayload(BaseModel):
    data: Any # Either Heartbeat or LogAnomaliCreate, will validate inside endpoint
    signature: str # HMAC-SHA256 signature for anti-tampering

class LogAnomaliResponse(BaseModel):
    id: int
    peserta_id: int
    tipe_anomali: str
    metadata_log: Optional[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        orm_mode = True
        
class ParticipantResponse(BaseModel):
    id: int
    user_id: int
    sesi_id: int
    agent_status: str
    last_heartbeat: Optional[datetime]
    
    class Config:
        orm_mode = True
