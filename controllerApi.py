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



def _client_link_config(user_id, port, public_key, server_name, short_id, host_name):
    return {
        "log": {},
        "inbounds": [
            {
                "settings": {
                    "udp": True,
                    "userLevel": 8,
                    "auth": "noauth",
                },
                "listen": "127.0.0.1",
                "port": 10808,
                "tag": "socks",
                "protocol": "socks",
            },
            {
                "settings": {
                    "userLevel": 8,
                    "udp": True,
                    "auth": "noauth",
                },
                "listen": "127.0.0.1",
                "port": 1087,
                "tag": "directSocks",
                "protocol": "socks",
            },
            {
                "settings": {
                    "address": "[::1]",
                },
                "listen": "[::1]",
                "port": 62789,
                "tag": "api",
                "protocol": "dokodemo-door",
            },
        ],
        "outbounds": [
            {
                "tag": "proxy",
                "protocol": "vless",
                "streamSettings": {
                    "sockopt": {
                        "dialerProxy": "fragment",
                        "tcpNoDelay": True,
                    },
                    "network": "tcp",
                    "security": "reality",
                    "tcpSettings": {
                        "header": {
                            "type": "none",
                        },
                    },
                    "realitySettings": {
                        "publicKey": public_key,
                        "serverName": server_name,
                        "show": False,
                        "mldsa65Verify": "",
                        "spiderX": "",
                        "shortId": short_id,
                        "fingerprint": "firefox",
                    },
                },
                "settings": {
                    "vnext": [
                        {
                            "port": port,
                            "users": [
                                {
                                    "encryption": "none",
                                    "flow": "xtls-rprx-vision",
                                    "id": user_id,
                                    "level": 8,
                                    "email": "",
                                },
                            ],
                            "address": host_name,
                        },
                    ],
                },
                "mux": {
                    "concurrency": 50,
                    "xudpConcurrency": 128,
                    "xudpProxyUDP443": "allow",
                    "enabled": False,
                },
            },
            {
                "settings": {
                    "userLevel": 8,
                    "fragment": {
                        "length": "80-250",
                        "interval": "10-100",
                        "packets": "tlshello",
                    },
                },
                "streamSettings": {
                    "sockopt": {
                        "tcpNoDelay": True,
                    },
                },
                "tag": "fragment",
                "protocol": "freedom",
            },
        ],
        "api": {
            "tag": "api",
            "services": [
                "StatsService",
            ],
        },
        "dns": {
            "queryStrategy": "UseIP",
            "servers": [
                {
                    "address": "8.8.8.8",
                    "skipFallback": False,
                },
            ],
            "tag": "dnsQuery",
            "disableCache": True,
            "disableFallbackIfMatch": True,
            "hosts": {
                "dns.quad9.net": [
                    "9.9.9.9",
                    "149.112.112.112",
                    "2620:fe::fe",
                    "2620:fe::9",
                ],
                "one.one.one.one": [
                    "1.1.1.1",
                    "1.0.0.1",
                    "2606:4700:4700::1111",
                    "2606:4700:4700::1001",
                ],
                "dns.google": [
                    "8.8.8.8",
                    "8.8.4.4",
                    "2001:4860:4860::8888",
                    "2001:4860:4860::8844",
                ],
                "cloudflare-dns.com": [
                    "104.16.248.249",
                    "104.16.249.249",
                    "2606:4700::6810:f8f9",
                    "2606:4700::6810:f9f9",
                ],
                "dns.alidns.com": [
                    "223.5.5.5",
                    "223.6.6.6",
                    "2400:3200::1",
                    "2400:3200:baba::1",
                ],
                "dns.cloudflare.com": [
                    "104.16.132.229",
                    "104.16.133.229",
                    "2606:4700::6810:84e5",
                    "2606:4700::6810:85e5",
                ],
                "common.dot.dns.yandex.net": [
                    "77.88.8.8",
                    "77.88.8.1",
                    "2a02:6b8::feed:0ff",
                    "2a02:6b8:0:1::feed:0ff",
                ],
                "dot.pub": [
                    "1.12.12.12",
                    "120.53.53.53",
                ],
            },
            "disableFallback": True,
        },
        "stats": {},
        "routing": {
            "balancers": [],
            "domainStrategy": "AsIs",
            "rules": [
                {
                    "type": "field",
                    "outboundTag": "direct",
                    "domain": [
                        "geosite:private",
                        "geosite:apple",
                    ],
                    "ruleTag": "rule-0",
                },
                {
                    "type": "field",
                    "inboundTag": [
                        "api",
                    ],
                    "outboundTag": "api",
                    "ruleTag": "rule-1",
                },
                {
                    "type": "field",
                    "inboundTag": [
                        "dnsQuery",
                    ],
                    "outboundTag": "proxy",
                    "ruleTag": "rule-2",
                },
                {
                    "type": "field",
                    "inboundTag": [
                        "directSocks",
                    ],
                    "outboundTag": "direct",
                    "ruleTag": "rule-3",
                },
                {
                    "type": "field",
                    "outboundTag": "direct",
                    "domain": [
                        "geosite:private",
                        "geosite:apple",
                    ],
                    "ruleTag": "rule-4",
                },
                {
                    "type": "field",
                    "inboundTag": [
                        "api",
                    ],
                    "outboundTag": "api",
                    "ruleTag": "rule-5",
                },
                {
                    "type": "field",
                    "inboundTag": [
                        "dnsQuery",
                    ],
                    "outboundTag": "proxy",
                    "ruleTag": "rule-6",
                },
                {
                    "type": "field",
                    "inboundTag": [
                        "directSocks",
                    ],
                    "outboundTag": "direct",
                    "ruleTag": "rule-7",
                },
            ],
        },
        "policy": {
            "system": {
                "statsOutboundDownlink": True,
                "statsInboundUplink": True,
                "statsOutboundUplink": True,
                "statsInboundDownlink": True,
            },
            "levels": {
                "8": {
                    "statsUserUplink": False,
                    "handshake": 4,
                    "connIdle": 30,
                    "uplinkOnly": 1,
                    "bufferSize": 0,
                    "statsUserDownlink": False,
                    "downlinkOnly": 1,
                },
            },
        },
        "transport": {},
    }


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
        host_name = config['Xray']['hostName']
        link_config = _client_link_config(
            id,
            port,
            public_key,
            server_name,
            short_id,
            host_name,
        )
        link = json.dumps(link_config, ensure_ascii=False)
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
    

async def suspend_users(user_ids: set[int]) -> bool:
    """
        Приостанавливает пользователей на сервере
    """
    try:

        users: str = ' '.join([str(user_id) for user_id in user_ids])

        subprocess.check_output(
            (f"/root/easy-xray-main/ex.sh suspend {users}"),
            shell=True
        )
        return True
    except Exception as e:
        return False


async def del_users(user_ids: set[int]) -> bool:
    """
        Удаляет пользователей с сервера
    """
    try:

        users: str = ' '.join([str(user_id) for user_id in user_ids])

        subprocess.check_output(
            (f"/root/easy-xray-main/ex.sh del {users}"),
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
