from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from loguru import logger
import sys

from app import models
from app.database import engine, get_db
from app.routers import auth, telemetri

from fastapi.staticfiles import StaticFiles

# Setup basic loguru logger
logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

app = FastAPI(title="HIDS Online Exam API", version="1.0")

@app.on_event("startup")
async def startup_event():
    # Initialize DB tables asynchronously
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    logger.info("Database tables verified.")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "message": str(exc)},
    )

# Mount PWA static files
app.mount("/mobile", StaticFiles(directory="static"), name="mobile")

# Allow CORS for Portal Web / Dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Autentikasi"])
app.include_router(telemetri.router, prefix="/api/v1/telemetry", tags=["Telemetri HIDS"])

@app.get("/")
def root():
    return {"message": "Server HIDS Online Exam is running"}

@app.get("/seed")
async def seed_data(db: AsyncSession = Depends(get_db)):
    # Create dummy user
    user_result = await db.execute(select(models.User).where(models.User.username == "testuser"))
    user = user_result.scalars().first()
    if not user:
        user = models.User(username="testuser", password_hash="dummy")
        db.add(user)
        
    # Create dummy session
    sesi_result = await db.execute(select(models.SesiUjian).where(models.SesiUjian.pin_sesi == "1234"))
    sesi = sesi_result.scalars().first()
    if not sesi:
        sesi = models.SesiUjian(pin_sesi="1234", is_active=True)
        db.add(sesi)
        
    await db.commit()
    return {"message": "Dummy data seeded! Username: testuser, Password: (apa saja), PIN: 1234"}
