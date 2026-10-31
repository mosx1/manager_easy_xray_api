from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Column, Numeric
from sqlmodel import Field, SQLModel


class Users(SQLModel, table=True):
    telegram_id: int = Field(sa_column=Column(BigInteger, primary_key=True))
    name: str | None = None
    exit_date: datetime
    action: bool
    server_link: str
    server_id: int = Field(foreign_key="servers.id")
    server_desired: str | None = None
    paid: bool
    protocol: int
    statistic: str | None = None
    balance: Decimal | None = Field(default=None, sa_column=Column(Numeric, nullable=True))
    invited: int | None = Field(default=None, foreign_key="users.telegram_id")
