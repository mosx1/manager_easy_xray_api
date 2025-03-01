from fastapi import APIRouter
from routers import link, managerUsers


router = APIRouter()
router.include_router(link.router)
router.include_router(managerUsers.router)