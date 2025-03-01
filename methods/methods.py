from sqlalchemy.ext.asyncio import AsyncSession

from db.requests.security import getTocken



async def successAuth(db: AsyncSession, tocken: str) -> bool:
    if tocken == await getTocken(db):
        return True