from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.core import schemas, models
from app.core.database import get_db
from sqlalchemy.future import select
from app.api.utils.security import verify_hmac_signature
from app.api.services.telemetry_service import save_telemetry_log, process_heartbeat

router = APIRouter()

async def verify_telemetry_signature(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")
    
    # We verify the raw body string with HMAC
    is_valid = verify_hmac_signature(body.decode(), signature)
    if not is_valid:
        raise HTTPException(status_code=403, detail="Invalid signature")
    return body

@router.post("/log")
async def receive_telemetry_log(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    # 1. Verify HMAC
    raw_body = await verify_telemetry_signature(request)
    data = json.loads(raw_body)
    
    # 2. Parse and save Anomali Log
    try:
        log_data = schemas.LogAnomaliCreate(**data)
        return await save_telemetry_log(log_data, db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload format: {str(e)}")

@router.post("/heartbeat")
async def receive_heartbeat(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    # 1. Verify HMAC
    raw_body = await verify_telemetry_signature(request)
    data = json.loads(raw_body)
    
    # 2. Parse Heartbeat
    try:
        hb_data = schemas.Heartbeat(**data)
        return await process_heartbeat(hb_data, db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload format: {str(e)}")

@router.get("/history", response_model=list[schemas.LogAnomaliResponse])
async def get_telemetry_history(
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(models.LogAnomali).order_by(models.LogAnomali.created_at.desc()).limit(limit))
    return result.scalars().all()

@router.get("/participants", response_model=list[schemas.ParticipantResponse])
async def get_participants(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(models.PesertaUjian))
    return result.scalars().all()
