from fastapi import APIRouter, Depends

from fastapi.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_session

from methods.methods import successAuth
from methods.xray.config_server import backup_config_server

router = APIRouter()

@router.get("/backup_config")
async def _(token: str, db: AsyncSession = Depends(get_session)):

    if not await successAuth(db, token):
        return {'success': 'Ошибка авторизации'}

    await backup_config_server()

    return JSONResponse({"success": True})