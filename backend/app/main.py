"""FastAPI entrypoint for the eter-agent mailbox coordinator."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import init_db
from app.heartbeat import heartbeat_sweeper
from app.ws import router as ws_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
    force=True,
)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    log.info("=== eter-agent backend starting (env=%s) ===", settings.env)
    log.info("DATABASE_URL host: %s",
             (settings.database_url.split("@")[-1].split("/")[0]
              if "@" in settings.database_url else settings.database_url))
    await init_db()
    log.info("=== DB initialized, starting heartbeat sweeper ===")
    stop = asyncio.Event()
    task = asyncio.create_task(heartbeat_sweeper(stop))
    try:
        yield
    finally:
        stop.set()
        await task


app = FastAPI(
    title="eter-agent backend",
    version="0.1.0",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "eter-agent-backend"}


app.include_router(ws_router)
