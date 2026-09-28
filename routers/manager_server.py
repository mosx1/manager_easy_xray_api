from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from deps.auth import require_query_auth
from methods.xray.config_server import backup_config_server

router = APIRouter(dependencies=[Depends(require_query_auth)])


@router.get("/backup_config")
async def _():
    await backup_config_server()
    return JSONResponse({"success": True})
