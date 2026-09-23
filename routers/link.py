from fastapi import APIRouter, Depends

from controllerApi import create_link

from deps.auth import require_query_auth

router = APIRouter(dependencies=[Depends(require_query_auth)])

@router.get("/linkconf")
async def _(userId: int):
    """
        Отдает ссылку для конфигурации пользователя
    """
    return {"link": await create_link(str(userId))}