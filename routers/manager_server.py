from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from deps.auth import require_query_auth
from methods.xray.config_server import backup_config_server
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
        await easy_xray.push()
    except RuntimeError as error:
        return JSONResponse(
            {"success": False, "error": str(error)},
            status_code=404,
        )
    except EasyXrayError as error:
        return JSONResponse(
            {"success": False, "error": str(error)},
            status_code=400,
        )
    return JSONResponse({"success": True})
