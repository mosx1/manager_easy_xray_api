from pydantic import BaseModel


class DelUsers(BaseModel):
    user_ids: list[int]
    token: str


class AddUsers(BaseModel):
    user_ids: set[int]
    token: str