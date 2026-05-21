from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime

from app import models, schemas

async def save_telemetry_log(log_data: schemas.LogAnomaliCreate, db: AsyncSession):
    new_log = models.LogAnomali(
        peserta_id=log_data.peserta_id,
        tipe_anomali=log_data.tipe_anomali,
        metadata_log=log_data.metadata_log
    )
    db.add(new_log)
    await db.commit()
    return {"status": "success", "message": "Log saved"}

async def process_heartbeat(hb_data: schemas.Heartbeat, db: AsyncSession):
    peserta_result = await db.execute(select(models.PesertaUjian).where(models.PesertaUjian.id == hb_data.peserta_id))
    peserta = peserta_result.scalars().first()
    
    if peserta:
        peserta.last_heartbeat = datetime.fromtimestamp(hb_data.timestamp)
        peserta.agent_status = "active"
        await db.commit()
    
    return {"status": "success", "message": "Heartbeat received"}
