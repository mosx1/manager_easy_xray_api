import json

from app_config import load_config


async def getJsonConf(userId: str) -> str:
    """
        Возвращает json конфигурация пользователя по id
    """
    config = load_config()
    
    with open("{}config_client_{}.json".format(config['Paths']['jsonConfig'], userId)) as file:

        return json.loads(
            file.read()
        )