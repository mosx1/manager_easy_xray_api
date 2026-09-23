import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlmodel import SQLModel

from db.db import (
    checkDatabaseConnection,
    databaseReconnectLoop,
    engine,
)
from deps.auth import AuthenticationError
from methods.xray.general import EasyXray
from routers import router

logger = logging.getLogger(__name__)


async def restoreXrayLoop(stopEvent: asyncio.Event) -> None:
    while not stopEvent.is_set():
        try:
            await EasyXray().push()
            logger.info("Xray configuration restored and process started")
            return
        except Exception as error:
            logger.warning("Xray startup postponed: %s", error)

        try:
            await asyncio.wait_for(stopEvent.wait(), timeout=10)
        except TimeoutError:
            continue


@asynccontextmanager
async def lifespan(_: FastAPI):
    stopEvent = asyncio.Event()
    reconnectTask = asyncio.create_task(databaseReconnectLoop(stopEvent))
    restoreXrayTask = asyncio.create_task(restoreXrayLoop(stopEvent))
    yield
    stopEvent.set()
    for task in (reconnectTask, restoreXrayTask):
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    EasyXray.stop_xray()
    await engine.dispose()


app = FastAPI(lifespan=lifespan)


@app.exception_handler(AuthenticationError)
async def auth_exception_handler(_, __: AuthenticationError):
    return JSONResponse({"success": "Ошибка авторизации"}, 401)


app.include_router(router)


@app.get("/health")
async def health():
    databaseAvailable = await checkDatabaseConnection()
    xrayRunning = EasyXray.is_xray_running()
    statusCode = 200 if databaseAvailable else 503
    return JSONResponse(
        {
            "status": "ok" if statusCode == 200 else "unavailable",
            "database": databaseAvailable,
            "xray": xrayRunning,
        },
        status_code=statusCode,
    )


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
        workers=1
    )