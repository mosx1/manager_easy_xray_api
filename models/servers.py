from typing import Any

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field



class Servers(SQLModel, table=True):
    
    id: int = Field(primary_key=True)
    links: str = Field()


class Configs_Servers(SQLModel, table=True):

    id: int = Field(primary_key=True)
    server_id: int = Field(foreign_key="servers.id")
    config: dict[str, Any] = Field(sa_column=Column(JSONB))