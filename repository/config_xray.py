from sqlmodel import text

from sqlalchemy.ext.asyncio import AsyncSession

async def writeConfigDB(server_id: int, config: str, db: AsyncSession):
    await db.execute(
        text(
            "INSERT INTO configs_servers (server_id, config)" +
            f" VALUE ({server_id}, '{config}')"
        )
    )
    await db.commit()