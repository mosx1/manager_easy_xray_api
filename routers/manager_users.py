from typing import Annotated

from fastapi import APIRouter, Depends

from controllerApi import create_link, create_xhttp_link
from deps.auth import authenticated_body, require_query_auth
from entities.manager_users import DelUsers
from entities.statistic import RequestStatustic
from methods.xray.general import EasyXray, EasyXrayError
from methods.xray.statistic import get_statustic_to_users

router = APIRouter(tags=["users"])


@router.get(
    "/add",
    summary="Добавить пользователя в Xray",
    description=(
        "Добавляет пользователя в Xray и возвращает JSON-подписку для клиента (как /linkconf). "
        "Query: `user_id`, `token` (токен из таблицы securityhashs)."
    ),
    dependencies=[Depends(require_query_auth)],
)
async def add_user(user_id: int) -> dict:
    easy_xray = EasyXray()
    await easy_xray.add([str(user_id)])

    response: dict[str, str | bool] = {
        "success": True,
        "link": await create_link(str(user_id)),
    }
    if easy_xray._xhttp_enabled():
        try:
            response["xhttp_link"] = await create_xhttp_link(str(user_id))
        except EasyXrayError:
            pass
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
