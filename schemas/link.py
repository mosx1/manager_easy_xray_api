from pydantic import BaseModel



class LinkForApp(BaseModel):
    tocken: str
    userId: int