from sqlmodel import SQLModel, Field
from datetime import datetime



class SecurityHashs(SQLModel, table=True):
    
    hash: str = Field(primary_key=True)
    data: datetime = Field(default="now()")