from typing import Annotated

from fastapi import APIRouter, Depends

from controllerApi import resumeUser, suspend_users
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
    user_links = (await easy_xray.add([str(user_id)]))[0]

    if not user_links.reality:
        return {"success": False}

    response: dict[str, str | bool] = {
        "success": True,
        "link": user_links.reality,
    }
    if user_links.xhttp:
        response["xhttp_link"] = user_links.xhttp
    return response


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
    easy_xray = EasyXray()
    await easy_xray.remove_users([str(user_id) for user_id in data.user_ids])
    return {"success": True}


@router.post("/statistic")
async def _(
    data: Annotated[RequestStatustic, Depends(authenticated_body(RequestStatustic))],
):
    """
        Статистика входящего трафика по id пользователя
    """
    return {"link": get_statustic_to_users(data.user_ids)}
