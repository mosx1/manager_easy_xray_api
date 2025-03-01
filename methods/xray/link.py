import json

from configparser import ConfigParser



async def getJsonConf(userId: str) -> str:
    """
        Возвращает json конфигурация пользователя по id
    """
    config = ConfigParser()
    config.read("config.ini")
    
    with open("{}config_client_{}.json".format(config['Paths']['jsonConfig'], userId)) as file:

        return json.loads(
            file.read()
        )