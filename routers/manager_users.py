from typing import Annotated

from fastapi import APIRouter, Depends

from controllerApi import add_user, resumeUser, del_users, suspend_users
from deps.auth import authenticated_body, require_query_auth
from entities.manager_users import DelUsers, SuspendUsers
from entities.statistic import RequestStatustic
from methods.xray.statistic import get_statustic_to_users
from methods.xray.general import EasyXray

router = APIRouter()

query_auth_router = APIRouter(dependencies=[Depends(require_query_auth)])
router.include_router(query_auth_router)


@query_auth_router.get("/add")
async def _(user_id: int) -> dict:
    easy_xray = EasyXray()
    await easy_xray.add([str(user_id)])
    link = await add_user(user_id)

    if link:
        return {"success": True, "link": link}
    return {"success": False}


@query_auth_router.get("/resume")
async def _(userId: int):
    if await resumeUser(userId):
        return {"success": True}
    return {"success": False}


@router.post("/suspend")
async def _(
    data: Annotated[SuspendUsers, Depends(authenticated_body(SuspendUsers))],
) -> dict[str, bool]:
    if await suspend_users(data.user_ids):
        return {"success": True}
    return {"success": False}


@router.post("/del")
async def _(
    data: Annotated[DelUsers, Depends(authenticated_body(DelUsers))],
):
    if await del_users(data.user_ids):
        return {"success": True}
    return {"success": False}


@router.post("/statistic")
async def _(
    data: Annotated[RequestStatustic, Depends(authenticated_body(RequestStatustic))],
):
    """
        Статистика входящего трафика по id пользователя
    """
    return {"link": get_statustic_to_users(data.user_ids)}
