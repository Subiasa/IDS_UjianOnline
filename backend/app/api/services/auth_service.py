from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from datetime import timedelta
import random
import string

from app.core import models, schemas
from app.api.utils.security import (
    create_access_token, 
    ACCESS_TOKEN_EXPIRE_MINUTES, 
    get_password_hash, 
    verify_password
)

async def authenticate_agent(login_data: schemas.AgentLoginRequest, db: AsyncSession) -> schemas.AgentLoginResponse:
    # 1. Verify Sesi
    sesi_result = await db.execute(select(models.SesiUjian).where(models.SesiUjian.pin_sesi == login_data.pin_sesi))
    sesi = sesi_result.scalars().first()
    if not sesi or not sesi.is_active:
        raise HTTPException(status_code=401, detail="Sesi ujian tidak valid atau tidak aktif")
    
    # 2. Verify User
    user_result = await db.execute(select(models.User).where(models.User.username == login_data.username))
    user = user_result.scalars().first()
    if not user or not verify_password(login_data.password, user.password_hash):
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
        await db.flush()
    
    # Simpan ID dan data yang diperlukan sebelum ada kemungkinan session kedaluwarsa
    peserta_id = peserta.id
    sesi_id = sesi.id

    # 4. Generate Token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "peserta_id": peserta_id, "sesi_id": sesi_id},
        expires_delta=access_token_expires
    )

    # 5. Update Status
    peserta.agent_status = "active"
    await db.commit()

    return schemas.AgentLoginResponse(access_token=access_token, peserta_id=peserta_id)

async def create_credential(data: schemas.CredentialCreateRequest, db: AsyncSession) -> schemas.CredentialCreateResponse:
    # 1. Cek atau buat SesiUjian
    sesi_result = await db.execute(select(models.SesiUjian).where(models.SesiUjian.pin_sesi == data.pin_sesi))
    sesi = sesi_result.scalars().first()
    if not sesi:
        sesi = models.SesiUjian(pin_sesi=data.pin_sesi, is_active=True)
        db.add(sesi)
        await db.flush()
        
    # 2. Cek User
    user_result = await db.execute(select(models.User).where(models.User.username == data.username))
    user = user_result.scalars().first()
    if user:
        raise HTTPException(status_code=400, detail="Username sudah digunakan")
        
    # 3. Buat User baru dengan password hash
    user = models.User(username=data.username, password_hash=get_password_hash(data.password), role="peserta")
    db.add(user)
    # Important: flush here to generate user.id
    await db.flush()
    
    # 4. Hubungkan User dengan SesiUjian sebagai PesertaUjian
    peserta = models.PesertaUjian(user_id=user.id, sesi_id=sesi.id)
    db.add(peserta)
    await db.flush()
    
    await db.commit()
    return schemas.CredentialCreateResponse(
        message="Kredensial berhasil dibuat",
        username=user.username,
        pin_sesi=sesi.pin_sesi
    )

async def bulk_create_credentials(data: schemas.BulkCredentialCreateRequest, db: AsyncSession):
    # 1. Cek atau buat SesiUjian
    sesi_result = await db.execute(select(models.SesiUjian).where(models.SesiUjian.pin_sesi == data.pin_sesi))
    sesi = sesi_result.scalars().first()
    if not sesi:
        sesi = models.SesiUjian(pin_sesi=data.pin_sesi, is_active=True)
        db.add(sesi)
        await db.flush()
    
    hashed_password = get_password_hash(data.password_default)
    created_users = []

    for _ in range(data.count):
        # Generate random username suffix
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        username = f"peserta_{suffix}"
        
        # Check if exists (unlikely with 4 random chars, but safe)
        existing = await db.execute(select(models.User).where(models.User.username == username))
        if existing.scalars().first(): continue

        user = models.User(username=username, password_hash=hashed_password, role="peserta")
        db.add(user)
        await db.flush()
        
        peserta = models.PesertaUjian(user_id=user.id, sesi_id=sesi.id)
        db.add(peserta)
        created_users.append(username)

    await db.commit()
    return {
        "message": f"Berhasil membuat {len(created_users)} akun peserta",
        "users": created_users,
        "password_default": data.password_default
    }
