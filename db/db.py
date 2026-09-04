import asyncio
import logging
from configparser import ConfigParser

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

RECONNECT_INTERVAL_SECONDS = 10

config = ConfigParser()
config.read("config.ini")

databaseUrl = "{}+{}://{}:{}@{}/{}".format(
    config["DataBase"]["dialect"],
    config["DataBase"]["driver"],
    config["DataBase"]["username"],
    config["DataBase"]["password"],
    config["DataBase"]["host"],
    config["DataBase"]["database"],
)

engine = create_async_engine(
    databaseUrl,
    pool_pre_ping=True,
)

async_session = sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

_dbAvailable = True


async def checkDatabaseConnection() -> bool:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except (SQLAlchemyError, OSError):
        return False


async def databaseReconnectLoop(stopEvent: asyncio.Event) -> None:
    global _dbAvailable

    while not stopEvent.is_set():
        connected = await checkDatabaseConnection()

        if connected:
            if not _dbAvailable:
                logger.info("Database connection restored")
            _dbAvailable = True
        else:
            if _dbAvailable:
                logger.warning(
                    "Database connection lost, retrying every %s seconds",
                    RECONNECT_INTERVAL_SECONDS,
                )
            _dbAvailable = False
            await engine.dispose()

        try:
            await asyncio.wait_for(stopEvent.wait(), timeout=RECONNECT_INTERVAL_SECONDS)
            return
        except TimeoutError:
            continue


async def get_session():
    async with async_session() as session:
        yield session
