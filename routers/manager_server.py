from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from deps.auth import require_query_auth
from methods.xray.config_server import (
    ConfigServer,
    ConfigServerAmbiguousError,
    ConfigServerNotFoundError,
    backup_config_server,
)
from methods.xray.general import EasyXray, EasyXrayError

router = APIRouter(
    dependencies=[Depends(require_query_auth)],
    tags=["server"],
)


@router.get("/backup_config", summary="Сохранить config.json Xray в БД")
async def backup_config():
    await backup_config_server()
    return JSONResponse({"success": True})


@router.post(
    "/apply_config",
    summary="Применить конфиг Xray из БД на сервер",
    description=(
        "Читает конфигурацию сервера из БД (Configs_Servers), записывает в "
        "`/usr/local/etc/xray/config.json`, устанавливает customgeo и перезапускает Xray. "
        "Query: `token`."
    ),
)
async def apply_config():
    easy_xray = EasyXray()
    try:
        _, server_id, update_date = await ConfigServer.get_with_meta()
        config_path = await easy_xray.push()
    except (ConfigServerNotFoundError, ConfigServerAmbiguousError) as error:
        return JSONResponse(
            {"success": False, "error": str(error)},
            status_code=404,
        )
    except EasyXrayError as error:
        return JSONResponse(
            {"success": False, "error": str(error)},
            status_code=400,
        )
    return JSONResponse(
        {
            "success": True,
            "server_id": server_id,
            "update_date": update_date.isoformat() if update_date else None,
            "config_path": str(config_path),
        }
    )
