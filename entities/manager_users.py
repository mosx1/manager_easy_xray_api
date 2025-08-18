from pydantic import BaseModel


class SuspendUsers(BaseModel):
    user_ids: set[int]
    token: str


class DelUsers(BaseModel):
    user_ids: set[int]
    token: str


class AddUsers(BaseModel):
    user_ids: set[int]
    token: str