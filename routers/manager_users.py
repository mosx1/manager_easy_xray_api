from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

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


@router.get(
    "/add_transit",
    summary="Добавить транзитного пользователя Xray без записи в БД",
    description=(
        "Добавляет пользователя только в локальный config.json Xray. "
        "Строка сервера в БД не нужна. "
        "Возвращает два outbound — `xhttp` и `tls` — их нужно вставить в "
        "`outbounds` другого сервера и направить на них routing, чтобы "
        "трафик шёл через этот узел. "
        "XHTTP слушает внутренний порт (по умолчанию 9443), наружу его "
        "отдаёт nginx на `public_port` (8443). "
        "TLS — VLESS TCP на порту `[Tls] port` (по умолчанию 2053), "
        "сертификат Let's Encrypt для домена. "
        "Query: `user_id`, `token`."
    ),
    dependencies=[Depends(require_query_auth)],
)
async def add_transit_user(user_id: str):
    easy_xray = EasyXray()
    try:
        created = await easy_xray.add_transit_user(user_id)
    except EasyXrayError as error:
        return JSONResponse(
            {"success": False, "error": str(error)},
            status_code=400,
        )
    return {"success": True, **created}


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
