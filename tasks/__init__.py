import asyncio

from tasks.config_server import backup_config_server

async def start_tasks():
    asyncio.create_task(backup_config_server())