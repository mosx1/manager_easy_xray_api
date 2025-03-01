from models.security import SecurityHashs

from sqlmodel import select

from sqlalchemy.ext.asyncio import AsyncSession



async def getTocken(db: AsyncSession) -> str:
    resDb = await db.execute(select(SecurityHashs))
    return resDb.fetchone()[0].hash