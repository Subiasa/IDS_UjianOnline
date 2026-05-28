from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import schemas
from app.core.database import get_db
from app.api.services.auth_service import authenticate_agent

router = APIRouter()

@router.post("/agent-login", response_model=schemas.AgentLoginResponse)
async def agent_login(login_data: schemas.AgentLoginRequest, db: AsyncSession = Depends(get_db)):
    return await authenticate_agent(login_data, db)

@router.post("/bulk-create-credential")
async def bulk_create_credential_endpoint(data: schemas.BulkCredentialCreateRequest, db: AsyncSession = Depends(get_db)):
    from app.api.services.auth_service import bulk_create_credentials
    return await bulk_create_credentials(data, db)

@router.post("/create-credential", response_model=schemas.CredentialCreateResponse)
async def create_credential_endpoint(data: schemas.CredentialCreateRequest, db: AsyncSession = Depends(get_db)):
    from app.api.services.auth_service import create_credential
    return await create_credential(data, db)
