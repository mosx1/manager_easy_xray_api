from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from deps.auth import require_query_auth
from methods.xray.config_server import backup_config_server
from methods.xray.general import EasyXray

router = APIRouter(dependencies=[Depends(require_query_auth)])


@router.get("/backup_config")
async def _():
    await backup_config_server()
    return JSONResponse({"success": True})


@router.get("/install_xray")
async def install_xray():
    easy_xray = EasyXray()
    easy_xray.install_xray()
    return JSONResponse({"success": True})
