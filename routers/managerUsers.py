from fastapi import APIRouter, Depends

from controllerApi import add_user, suspendUser, resumeUser, del_users

from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_session

from methods.methods import successAuth
from methods.xray.statistic import get_statustic_to_users

from entities.statistic import RequestStatustic
from entities.manager_users import DelUsers


router = APIRouter()



@router.get("/add")
async def _(token: str, user_id: int, db: AsyncSession = Depends(get_session)) -> dict:
    if not await successAuth(db, token):
        return {'success': 'Ошибка авторизации'}
    
    link  = await add_user(user_id)

    if link:
        return {"success": True, "link": link}
    return {"success": False}



@router.get("/suspend")
async def _(token: str, userId: int, db: AsyncSession = Depends(get_session)):
    if not await successAuth(db, token):
        return {'success': 'Ошибка авторизации'}
    if await suspendUser(userId):
        return {"success": True}
    return{"success": False}



@router.get("/resume")
async def _(token: str, userId: int, db: AsyncSession = Depends(get_session)):
    if not await successAuth(db, token):
        return {'success': 'Ошибка авторизации'}
    if await resumeUser(userId):
        return {"success": True}
    return{"success": False}



@router.post("/del")
async def _(data: DelUsers, db: AsyncSession = Depends(get_session)):
    if not await successAuth(db, data.token):
        return {'success': 'Ошибка авторизации'}
    if await del_users(data.user_ids):
        return {"success": True}
    return{"success": False}



@router.post("/statistic")
async def _(data: RequestStatustic, db: AsyncSession = Depends(get_session)):
    """
        Статистика входящего трафика по id пользователя
    """
    if not await successAuth(db, data.token):
        return {'success': 'Ошибка авторизации'}
    return {"link": get_statustic_to_users(data.user_ids)}