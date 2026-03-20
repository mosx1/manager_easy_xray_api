from configparser import ConfigParser

from sqlalchemy import select, update, insert
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_session

from models.servers import Servers, ConfigsServers


async def get_id_server_by_hostname(host_name: str) -> int | None:
    session: AsyncSession = await get_session()
    server: Servers | None = await session.execute(select(Servers).where(Servers.links.ilike(f"%{host_name}%"))).scalar()
    return server.id


async def write_config(server_id: int, text_file: str):
    session: AsyncSession = await get_session()
    configs = await session.execute(select(ConfigsServers).where(ConfigsServers.server_id == server_id)).scalar()
    if configs:
        await session.execute(update(ConfigParser).where(ConfigsServers.server_id == server_id).values(config=text_file))
    else:
        await session.execute(
            insert(ConfigsServers).values(
                server_id=server_id,
                config=text_file
            )
        )
    await session.commit()


async def backup_config_server():
    
    config = ConfigParser()
    config.read("config.ini")

    server_id: int = await get_id_server_by_hostname(config["Xray"].get("hostName"))

    with open('/usr/local/etc/xray/config.json', 'r') as config_file:
        await write_config(server_id, config_file.read())