from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_session

from methods.methods import successAuth

from controllerApi import createLink


router = APIRouter()



@router.get("/linkforapp")
async def _(token: str, userId: int, db: AsyncSession = Depends(get_session)):
    """
        Отдает ссылку для конфигурации пользователя
    """
    if not await successAuth(db, token):
        return {'success': 'Ошибка авторизации'}
    return RedirectResponse(f"v2raytun://import/{ await createLink(str(userId))}")



@router.get("/linkconf")
async def _(token: str, userId: int, db: AsyncSession = Depends(get_session)):
    """
        Отдает ссылку для конфигурации пользователя
    """
    if not await successAuth(db, token):
        return {'success': 'Ошибка авторизации'}
    return {"link": await createLink(str(userId))}