from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_session

from methods.methods import successAuth

from controllerApi import create_link


router = APIRouter(dependencies=[Depends(require_query_auth)])


@router.get("/linkforapp")
async def _(userId: int):
    """
        Отдает ссылку для конфигурации пользователя
    """
    if not await successAuth(db, token):
        return {'success': 'Ошибка авторизации'}
    return RedirectResponse(f"v2raytun://import/{ await create_link(str(userId))}")



@router.get("/linkconf")
async def _(userId: int):
    """
        Отдает ссылку для конфигурации пользователя
    """
    if not await successAuth(db, token):
        return {'success': 'Ошибка авторизации'}
    return {"link": await create_link(str(userId))}