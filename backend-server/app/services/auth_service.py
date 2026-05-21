from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from datetime import timedelta

from app import models, schemas
from app.utils.security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

async def authenticate_agent(login_data: schemas.AgentLoginRequest, db: AsyncSession) -> schemas.AgentLoginResponse:
    # 1. Verify Sesi
    sesi_result = await db.execute(select(models.SesiUjian).where(models.SesiUjian.pin_sesi == login_data.pin_sesi))
    sesi = sesi_result.scalars().first()
    if not sesi or not sesi.is_active:
        raise HTTPException(status_code=401, detail="Sesi ujian tidak valid atau tidak aktif")
    
    # 2. Verify User
    user_result = await db.execute(select(models.User).where(models.User.username == login_data.username))
    user = user_result.scalars().first()
    if not user:
        raise HTTPException(status_code=401, detail="Kredensial tidak valid")
    
    # 3. Find or Create PesertaUjian
    peserta_result = await db.execute(
        select(models.PesertaUjian).where(
            models.PesertaUjian.user_id == user.id,
            models.PesertaUjian.sesi_id == sesi.id
        )
    )
    peserta = peserta_result.scalars().first()

    if not peserta:
        peserta = models.PesertaUjian(user_id=user.id, sesi_id=sesi.id)
        db.add(peserta)
        await db.commit()
        await db.refresh(peserta)
    
    # 4. Generate Token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "peserta_id": peserta.id, "sesi_id": sesi.id},
        expires_delta=access_token_expires
    )

    # 5. Update Status
    peserta.agent_status = "active"
    await db.commit()

    return schemas.AgentLoginResponse(access_token=access_token, peserta_id=peserta.id)
