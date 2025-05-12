from pydantic import BaseModel

from enum import Enum


class TrafficType(Enum):
    uplink: str = 'uplink'
    downlink: str = 'downlink'


class RequestStatustic(BaseModel):
    user_ids: set[int]
    token: str