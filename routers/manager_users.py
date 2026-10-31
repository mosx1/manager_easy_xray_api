from typing import Annotated

from fastapi import APIRouter, Depends

from deps.auth import authenticated_body, require_query_auth
from entities.manager_users import DelUsers
from entities.statistic import RequestStatustic
from methods.xray.statistic import get_statustic_to_users
from methods.xray.general import EasyXray

router = APIRouter(tags=["users"])


@router.get(
    "/add",
    summary="Добавить пользователя в Xray",
    description=(
        "Создаёт или возвращает VLESS-ссылки (Reality и при включённом XHTTP — xhttp_link). "
        "Query: `user_id`, `token` (токен из таблицы securityhashs)."
    ),
    dependencies=[Depends(require_query_auth)],
)
async def add_user(user_id: int) -> dict:
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


@router.post("/del", summary="Удалить пользователей из Xray")
async def delete_users(
    data: Annotated[DelUsers, Depends(authenticated_body(DelUsers))],
):
    easy_xray = EasyXray()
    await easy_xray.remove_users([str(user_id) for user_id in data.user_ids])
    return {"success": True}


@router.post(
    "/statistic",
    summary="Статистика трафика по пользователям",
)
async def user_statistic(
    data: Annotated[RequestStatustic, Depends(authenticated_body(RequestStatustic))],
):
    return {"link": get_statustic_to_users(data.user_ids)}
