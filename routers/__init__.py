from fastapi import APIRouter
from routers import link, manager_server, managerUsers


router = APIRouter()
router.include_router(link.router)
router.include_router(managerUsers.router)
router.include_router(manager_server.router)