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
    
    body_str = body.decode()
    try:
        data = json.loads(body_str)
        timestamp = data.get("timestamp")
    except:
        timestamp = None

    # We verify the raw body string with HMAC
    is_valid = verify_hmac_signature(body_str, signature, timestamp)
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
    # Join PesertaUjian with User to get username
    result = await db.execute(
        select(models.PesertaUjian, models.User.username)
        .join(models.User, models.PesertaUjian.user_id == models.User.id)
    )
    participants = []
    for peserta, username in result:
        p_data = schemas.ParticipantResponse.from_orm(peserta).dict()
        p_data["username"] = username
        participants.append(p_data)
    return participants

@router.delete("/participants/{peserta_id}")
async def delete_participant(
    peserta_id: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        # 1. Get participant
        result = await db.execute(select(models.PesertaUjian).where(models.PesertaUjian.id == peserta_id))
        peserta = result.scalars().first()
        if not peserta:
            raise HTTPException(status_code=404, detail="Peserta tidak ditemukan")
        
        user_id = peserta.user_id
        
        # 2. Delete logs associated with this participant
        from sqlalchemy import delete
        await db.execute(delete(models.LogAnomali).where(models.LogAnomali.peserta_id == peserta_id))
        
        # 3. Delete participant record
        await db.delete(peserta)
        
        # 4. Delete the User record
        user_result = await db.execute(select(models.User).where(models.User.id == user_id))
        user = user_result.scalars().first()
        if user:
            await db.delete(user)
            
        await db.commit()
        return {"message": f"Peserta {peserta_id} dan akun user berhasil dihapus."}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Gagal menghapus peserta: {str(e)}")

@router.post("/reset-all")
async def reset_all_data(
    db: AsyncSession = Depends(get_db)
):
    try:
        from sqlalchemy import delete
        # Delete only the anomaly logs
        await db.execute(delete(models.LogAnomali))
        
        await db.commit()
        return {"message": "Semua data log kecurangan berhasil dibersihkan. Data peserta tetap aman."}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Gagal meriset data: {str(e)}")
