from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas
from app.database import get_db
from app.services.auth_service import authenticate_agent

router = APIRouter()

@router.post("/agent-login", response_model=schemas.AgentLoginResponse)
async def agent_login(login_data: schemas.AgentLoginRequest, db: AsyncSession = Depends(get_db)):
    return await authenticate_agent(login_data, db)
