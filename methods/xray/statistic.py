import json, subprocess

from entities.statistic import TrafficType


def get_traffic(type: TrafficType) -> int:
    downlink: str = subprocess.check_output(
        f'echo $(xray api stats -server=127.0.0.1:8080 -name "outbound>>>direct>>>traffic>>>downlink" 2> /dev/null)', 
        universal_newlines=True,
        shell=True
    )
    try:
        downlink_json = json.loads(downlink)
    except Exception:
        return 0

    if 'stat' in downlink_json:
        return downlink_json['stat']['value']
    else:
        return 0


def get_traffic_by_user(user_id: int, type: TrafficType) -> int:
    downlink: str = subprocess.check_output(
        f'echo $(xray api stats -server=127.0.0.1:8080 -name "user>>>{user_id}@example.com>>>traffic>>>{type.value}" 2> /dev/null)', 
        universal_newlines=True,
        shell=True
    )
    try:
        downlink_json = json.loads(downlink)
    except Exception:
        return 0

    if 'stat' in downlink_json:
        return downlink_json['stat']['value']
    else:
        return 0


def get_statustic_to_users(user_ids: set) -> dict:
    
    users_to_traffic: dict = {}

    for user_id in user_ids:
        users_to_traffic[user_id] = {}
        users_to_traffic[user_id]['downlink'] = get_traffic_by_user(user_id, TrafficType.downlink)
        users_to_traffic[user_id]['uplink'] = get_traffic_by_user(user_id, TrafficType.uplink)
    
    return users_to_traffic