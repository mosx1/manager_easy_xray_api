import uvicorn, http

from fastapi import FastAPI

from db.db import engine

from sqlmodel import SQLModel

from routers import router


app = FastAPI()

app.include_router(router)



@app.get("/config")
async def _():
    
    return{"Glory to Russia": "FUCK YOU"}


@app.get("/initdb/")
async def _():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)



if __name__ == "__main__":
    conn = http.client.HTTPConnection("ifconfig.me")
    conn.request("GET", "/ip")
    url = conn.getresponse().read().decode("utf-8")  
    uvicorn.run(
        "main:app",
        host=url,
        port=8081,
        reload=False
    )