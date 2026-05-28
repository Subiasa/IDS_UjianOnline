from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String, default="peserta") # "peserta" or "pengawas"

class SesiUjian(Base):
    __tablename__ = "sesi_ujian"
    id = Column(Integer, primary_key=True, index=True)
    pin_sesi = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PesertaUjian(Base):
    __tablename__ = "peserta_ujian"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    sesi_id = Column(Integer, ForeignKey("sesi_ujian.id"))
    agent_status = Column(String, default="inactive") # "inactive", "active", "disconnected"
    last_heartbeat = Column(DateTime(timezone=True))

class LogAnomali(Base):
    __tablename__ = "log_anomali"
    id = Column(Integer, primary_key=True, index=True)
    peserta_id = Column(Integer, ForeignKey("peserta_ujian.id"))
    tipe_anomali = Column(String) # "WINDOW_SWITCHING", "CLIPBOARD_USAGE", "BLACKLISTED_PROCESS"
    metadata_log = Column(JSON) # Pydantic dict / JSONB fallback for sqlite compatibility
    created_at = Column(DateTime(timezone=True), server_default=func.now())
