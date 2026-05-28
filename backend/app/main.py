from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from loguru import logger
import sys

from app.core import models
from app.core.database import engine, get_db
from app.api.routers import auth, telemetri, websocket

from fastapi.staticfiles import StaticFiles

# Setup basic loguru logger
logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

app = FastAPI(title="HIDS Online Exam API", version="1.0")

@app.on_event("startup")
async def startup_event():
    # In async environments with SQLAlchemy 2.0, metadata.create_all 
    # should be called in a run_sync block on the engine
    async with engine.begin() as conn:
        # await conn.run_sync(models.Base.metadata.drop_all) # Only for debugging
        await conn.run_sync(models.Base.metadata.create_all)
    logger.info("Database connection established and tables verified.")

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
app.include_router(websocket.router, tags=["WebSockets"])

from fastapi.responses import RedirectResponse

@app.get("/")
def root():
    return RedirectResponse(url="/mobile/dashboard.html")

@app.get("/seed")
async def seed_data(db: AsyncSession = Depends(get_db)):
    from app.api.utils.security import get_password_hash
    # Create dummy user
    user_result = await db.execute(select(models.User).where(models.User.username == "testuser"))
    user = user_result.scalars().first()
    if not user:
        user = models.User(username="testuser", password_hash=get_password_hash("password123"))
        db.add(user)
        
    # Create dummy session
    sesi_result = await db.execute(select(models.SesiUjian).where(models.SesiUjian.pin_sesi == "1234"))
    sesi = sesi_result.scalars().first()
    if not sesi:
        sesi = models.SesiUjian(pin_sesi="1234", is_active=True)
        db.add(sesi)
        
    await db.commit()
    return {"message": "Dummy data seeded! Username: testuser, Password: (apa saja), PIN: 1234"}
