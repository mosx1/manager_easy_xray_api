from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from controllerApi import create_link
from deps.auth import require_query_auth

router = APIRouter(dependencies=[Depends(require_query_auth)])


@router.get("/linkforapp")
async def _(userId: int):
    """
        Отдает ссылку для конфигурации пользователя
    """
    return RedirectResponse(f"v2raytun://import/{await create_link(str(userId))}")


@router.get("/linkconf")
async def _(userId: int):
    """
        Отдает ссылку для конфигурации пользователя
    """
    return {"link": await create_link(str(userId))}
