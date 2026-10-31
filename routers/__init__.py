from fastapi import APIRouter
from routers import link, manager_server, manager_users


router = APIRouter()
router.include_router(link.router)
router.include_router(manager_users.router)
router.include_router(manager_server.router)