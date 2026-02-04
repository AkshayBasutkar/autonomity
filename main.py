from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import router
from app.services.session_store import session_store

app = FastAPI(title="Agentic Honeypot API")
app.include_router(router)


@app.on_event("startup")
async def on_startup() -> None:
    await session_store.connect()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await session_store.close()