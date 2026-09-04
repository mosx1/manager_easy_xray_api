import asyncio
import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from db.db import databaseReconnectLoop, engine
from deps.auth import AuthenticationError
from sqlmodel import SQLModel

from routers import router


@asynccontextmanager
async def lifespan(_: FastAPI):
    stopEvent = asyncio.Event()
    reconnectTask = asyncio.create_task(databaseReconnectLoop(stopEvent))
    yield
    stopEvent.set()
    reconnectTask.cancel()
    try:
        await reconnectTask
    except asyncio.CancelledError:
        pass
    await engine.dispose()


app = FastAPI(lifespan=lifespan)


@app.exception_handler(AuthenticationError)
async def auth_exception_handler(_, __: AuthenticationError):
    return JSONResponse({"success": "Ошибка авторизации"}, 401)


app.include_router(router)

@app.get("/config")
async def _():
    
    return{"Glory to Russia": "FUCK YOU"}


@app.get("/initdb/")
async def _():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)



if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8081,
        reload=False,
        workers=2
    )