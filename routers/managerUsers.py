from fastapi import APIRouter, Depends

from controllerApi import add_vpn_user, suspendUser, resumeUser, delUser

from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_session

from methods.methods import successAuth


router = APIRouter()



@router.get("/add")
async def _(token: str, userId: int, db: AsyncSession = Depends(get_session)):
    if not await successAuth(db, token):
        return {'success': 'Ошибка авторизации'}
    
    link  = await add_vpn_user(str(userId))

    if link:
        return {"success": True, "link": link}
    return {"success": False}



@router.get("/suspend")
async def _(token: str, userId: int, db: AsyncSession = Depends(get_session)):
    if not await successAuth(db, token):
        return {'success': 'Ошибка авторизации'}
    if suspendUser(userId):
        return {"success": True}
    return{"success": False}



@router.get("/resume")
async def _(token: str, userId: int, db: AsyncSession = Depends(get_session)):
    if not await successAuth(db, token):
        return {'success': 'Ошибка авторизации'}
    if resumeUser(userId):
        return {"success": True}
    return{"success": False}



@router.get("/del")
async def _(token: str, userId: int, db: AsyncSession = Depends(get_session)):
    if not await successAuth(db, token):
        return {'success': 'Ошибка авторизации'}
    if delUser(userId):
        return {"success": True}
    return{"success": False}