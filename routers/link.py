from fastapi import APIRouter, Depends

from controllerApi import create_link

from deps.auth import require_query_auth

router = APIRouter(
    dependencies=[Depends(require_query_auth)],
    tags=["links"],
)

@router.get("/linkconf", summary="JSON конфиг клиента (Reality) для v2rayTun")
async def link_conf(userId: int):
    return {"link": await create_link(str(userId))}