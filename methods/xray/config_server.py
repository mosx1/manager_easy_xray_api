import json
from datetime import datetime

from sqlalchemy import insert, select, update

from app_config import load_config
from db.db import async_session
from models.servers import Configs_Servers, Servers


class ConfigServerNotFoundError(RuntimeError):
    """Server or stored Xray config row could not be resolved."""


class ConfigServerAmbiguousError(RuntimeError):
    """Several servers match hostName from config.ini."""


class ConfigServer:

    @classmethod
    async def write(cls, text: dict | str):
        config_data = json.loads(text) if isinstance(text, str) else text
        server_id = await get_id_server_by_hostname()
        updated_at = datetime.now().replace(tzinfo=None)
        async with async_session() as session:
            configs = await session.execute(
                select(Configs_Servers).where(Configs_Servers.server_id == server_id)
            )
            configs = configs.scalar()
            if configs:
                await session.execute(
                    update(Configs_Servers)
                    .where(Configs_Servers.server_id == server_id)
                    .values(config=config_data, update_date=updated_at)
                )
            else:
                await session.execute(
                    insert(Configs_Servers).values(
                        server_id=server_id,
                        config=config_data,
                        update_date=updated_at,
                    )
                )
            await session.commit()

    @classmethod
    async def get(cls) -> dict:
        config, _, _ = await cls.get_with_meta()
        return config

    @classmethod
    async def get_with_meta(cls) -> tuple[dict, int, datetime | None]:
        server_id = await get_id_server_by_hostname()
        async with async_session() as session:
            row = await session.execute(
                select(Configs_Servers).where(Configs_Servers.server_id == server_id)
            )
            configs = row.scalar()
            if configs is None:
                raise ConfigServerNotFoundError(
                    f"Конфигурация Xray не найдена в БД для server_id={server_id}"
                )
            raw = configs.config
            if isinstance(raw, str):
                parsed = json.loads(raw)
            else:
                parsed = raw
            return parsed, server_id, configs.update_date


async def get_id_server_by_hostname(host_name: str | None = None) -> int:
    if not host_name:
        host_name = load_config()["Xray"].get("hostName", "").strip()
    if not host_name:
        raise ConfigServerNotFoundError(
            "Xray.hostName не задан в config.ini — нельзя определить server_id"
        )

    async with async_session() as session:
        result = await session.execute(
            select(Servers).where(Servers.links.ilike(f"%{host_name}%"))
        )
        servers = list(result.scalars().all())

    if not servers:
        raise ConfigServerNotFoundError(
            f"В таблице servers нет записи с links, содержащим {host_name!r}"
        )
    if len(servers) > 1:
        ids = ", ".join(str(server.id) for server in servers)
        raise ConfigServerAmbiguousError(
            f"Несколько servers ({ids}) подходят под hostName {host_name!r}; "
            "уточните поле links"
        )
    return servers[0].id


async def backup_config_server():
    from app_config import xray_config_file_path

    path = xray_config_file_path()
    with open(path, encoding="utf-8") as config_file:
        await ConfigServer.write(config_file.read())
