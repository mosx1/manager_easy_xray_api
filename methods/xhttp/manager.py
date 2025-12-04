import json, random, string, os, secrets

from configparser import ConfigParser

from urllib.parse import quote

from repository.config_xray import writeConfigDB

class ManagerConfig:

    path_file = '/usr/local/etc/xray/config.json'

    @classmethod
    def _get_rand_str(cls, length:int) -> str:
        chars = string.ascii_lowercase + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    

    @classmethod
    async def add(cls, user_id: str) -> str | None:

        config_xray_data = None

        with open(cls.path_file) as config_xray_file:

            if link := cls.get_link(user_id):
                return link 

            config_xray_data: dict = json.load(config_xray_file)
            client_id: str = '{}-{}-{}-{}-{}'.format(
                cls._get_rand_str(8),
                cls._get_rand_str(4),
                cls._get_rand_str(4),
                cls._get_rand_str(4),
                cls._get_rand_str(12)
            )
            short_id: str = secrets.token_hex(16)
            
            client: dict = config_xray_data['inbounds'][0]['settings']['clients'][0].copy()
            client['id'] = client_id
            client['email'] = f"{user_id}@kuzmos.ru"
            config_xray_data['inbounds'][0]['settings']['clients'].append(client)
            config_xray_data['inbounds'][0]['streamSettings']['realitySettings']['shortIds'].append(short_id)
            config_xray_data['inbounds'][1]['settings']['clients'].append({"id": client_id})

        with open(cls.path_file, "w") as config_xray_file:
            json.dump(config_xray_data, config_xray_file, indent=4)
        
        os.system('service xray restart')

        return cls.get_link(user_id)

    @classmethod
    def get_link(cls, user_id: str) -> str | None:

        client_data = {}

        with open(cls.path_file) as config_xray_file:
            config_xray_data: dict = json.load(config_xray_file)
            for i, client in enumerate(config_xray_data['inbounds'][0]['settings']['clients']):
                if client['email'] == f"{user_id}@kuzmos.ru":
                    client_data['sid'] = config_xray_data['inbounds'][0]['streamSettings']['realitySettings']['shortIds'][i]
                    client_data['id'] = client['id']

                    continue
            
            if client_data.get('id'):

                api_conf = ConfigParser()
                api_conf.read('config.ini')

                client_data['host'] = api_conf['Xray'].get('hostName')
                client_data['port'] = api_conf['Xray'].get('port')
                client_data['public_key'] = api_conf['Xray'].get('public_key')
                client_data['path'] = quote(config_xray_data['inbounds'][1]['streamSettings']['xhttpSettings']['path'], safe='')
                client_data['mode'] = config_xray_data['inbounds'][1]['streamSettings']['xhttpSettings']['mode']
                client_data['sni'] = config_xray_data['inbounds'][0]['streamSettings']['realitySettings']['serverNames'][0]
                client_data['psx'] = quote(config_xray_data['inbounds'][0]['streamSettings']['realitySettings']['spiderX'], safe='')
        
                return f"vless://{client_data['id']}@{client_data['host']}:{client_data['port']}?security=reality&type=xhttp&headerType=&path={client_data['path']}&host=&mode={client_data['mode']}&sni={client_data['sni']}&fp=chrome&pbk={client_data['public_key']}&sid={client_data['sid']}&psx={client_data['psx']}#{client_data['host']}"
    
    @classmethod
    def delete(cls, user_ids: list[str]) -> None:

        with open(cls.path_file) as config_xray_file:
            config_xray_data: dict = json.load(config_xray_file)
            xtls_clients: list = config_xray_data['inbounds'][0]['settings']['clients']
            xhttp_clients: list = config_xray_data['inbounds'][1]['settings']['clients']
            shortIds: list = config_xray_data['inbounds'][0]['streamSettings']['realitySettings']['shortIds']

        for i, client in enumerate(xtls_clients.copy()):
            for user_id in user_ids:
                if client['email'] == f"{user_id}@kuzmos.ru":

                    xtls_clients.remove(i)
                    xhttp_clients.remove(i)
                    shortIds.remove(i)

        config_xray_data['inbounds'][0]['settings']['clients'] = xtls_clients
        config_xray_data['inbounds'][1]['settings']['clients'] = xhttp_clients
        config_xray_data['inbounds'][0]['streamSettings']['realitySettings']['shortIds'] = shortIds

        with open(cls.path_file, "w") as config_xray_file:
            json.dump(config_xray_data, config_xray_file, indent=4)
        
        os.system('service xray restart')