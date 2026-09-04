import json

from configparser import ConfigParser

from sqlalchemy import insert, select, update

from db.db import async_session
from models.servers import Configs_Servers, Servers


class ConfigServer:

    @classmethod
    async def write(cls, text: dict | str):
        if isinstance(text, dict):
            text = json.dumps(text)
        server_id = await get_id_server_by_hostname()
        async with async_session() as session:
            configs = await session.execute(
                select(Configs_Servers).where(Configs_Servers.server_id == server_id)
            )
            configs = configs.scalar()
            if configs:
                await session.execute(
                    update(Configs_Servers)
                    .where(Configs_Servers.server_id == server_id)
                    .values(config=text)
                )
            else:
                await session.execute(
                    insert(Configs_Servers).values(
                        server_id=server_id,
                        config=text,
                    )
                )
            await session.commit()

    @classmethod
    async def get(cls) -> dict:
        server_id = await get_id_server_by_hostname()
        async with async_session() as session:
            configs = await session.execute(
                select(Configs_Servers).where(Configs_Servers.server_id == server_id)
            )
            configs = configs.scalar()
            return json.loads(configs.config)


async def get_id_server_by_hostname(host_name: str | None = None) -> int | None:
    if not host_name:
        config = ConfigParser()
        config.read("config.ini")
        host_name: str = config["Xray"].get("hostName")
    if host_name:
        async with async_session() as session:
            server: Servers | None = await session.execute(
                select(Servers).where(Servers.links.ilike(f"%{host_name}%"))
            )
            server = server.scalar()
            return server.id


async def backup_config_server():
    server_id = await get_id_server_by_hostname()
    with open("/usr/local/etc/xray/config.json", "r") as config_file:
        await ConfigServer.write(server_id, config_file.read())
