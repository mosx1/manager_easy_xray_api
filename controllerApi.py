import subprocess, json, os
from configparser import ConfigParser


async def add_user(user_id: int) -> str:
    """
        Создает пользоавтеля в xray
    """
    try:
        subprocess.check_output(
            (
                "/root/easy-xray-main/ex.sh add {}".format(user_id)
            ), 
            shell=True
        )
    except subprocess.CalledProcessError as e:
        return e.output

    return await createLink(user_id)



async def createLink(userId: str):
    """
        Создает ссылку для пользователя по конфигурации
    """

    config = ConfigParser()
    config.read("config.ini")

    with open("/root/easy-xray-main/conf/config_client_{}.json".format(userId)) as file:

        jsonData = json.load(file)

        id = jsonData["outbounds"][0]["settings"]["vnext"][0]["users"][0]["id"]
        port = jsonData["outbounds"][0]["settings"]["vnext"][0]["port"]
        public_key = jsonData["outbounds"][0]["streamSettings"]["realitySettings"]["publicKey"]
        server_name = jsonData["outbounds"][0]["streamSettings"]["realitySettings"]["serverName"]
        short_id = jsonData["outbounds"][0]["streamSettings"]["realitySettings"]["shortId"]

        link = "vless://{}@{}:{}?fragment=&security=reality&encryption=none&pbk={}&fp=chrome&type=tcp&flow=xtls-rprx-vision&sni={}&sid={}#vpnKuzMosDE1".format(
            id,
            config['Xray']['hostName'],
            port,
            public_key,
            server_name,
            short_id
        )
        return link
    


async def createLinkForApp(link: str):
    """
        Страница для настройки приложения
    """
    return """"
    <head>
        <meta http-equiv="refresh" content="0;URL=v2rayTun://import/{}" />
    </head>
   """.format(link)



async def suspendUser(userId: str) -> bool:
    """
        Приостонавливает пользователя в xray
    """
    try:
        subprocess.check_output(("/root/easy-xray-main/ex.sh suspend {}".format(userId)), shell=True)
        return True
    
    except subprocess.CalledProcessError as e:
        return False



async def resumeUser(userId: str):
    """
        Возобновляет доступ пользователя к xray
    """
    try:
        subprocess.check_output(("/root/easy-xray-main/ex.sh resume {}".format(userId)), shell=True)
        return True
    except subprocess.CalledProcessError as e:
        return False
    


async def del_users(user_ids: set[int]) -> bool:
    """
        Удаляет пользователей с сервера
    """
    try:

        subprocess.check_output(
            (
                "/root/easy-xray-main/ex.sh del",
                *[str(user_id) for user_id in user_ids]
            ),
            shell=True
        )
        return True
    except subprocess.CalledProcessError as e:
        return False
    



async def getStatistic():
    """
        Получает статистику по пользователям
        
    """

    dictRes = {}
    subprocess.check_output(("rm stats.log",), shell=True)
    os.system("/root/easy-xray-main/ex.sh stats")

    with open('stats.log') as fileLog:
        listReversFileLog = reversed(fileLog.readlines())
        for i in listReversFileLog:
            tempArrResult = i.split(' by ')
            if len(tempArrResult) > 1:
                
                arrResult = (tempArrResult[1]).split('@example.com')

                if arrResult[0] not in dictRes:
                    dictRes[arrResult[0]] = {}
                if len(arrResult) > 1:
                    dictRes[arrResult[0]][tempArrResult[0]] = arrResult[1][:-2]

        return dictRes
    


async def checkExistsUser(userId: str) -> bool:
    """
        Проверяет существует ли пользователь в файле конфигурации сервера
    """
    email = "{}@example.com".format(userId)

    with open('/usr/local/etc/xray/config.json', 'r') as configFile:
        configData = json.loads(configFile.read())
        clients = configData['inbounds'][1]['settings']['clients']
        for client in clients:
            if client['email'] == email:
                return True
    return False
