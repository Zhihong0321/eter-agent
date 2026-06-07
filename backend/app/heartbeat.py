"""Department online/offline tracking.

A lightweight periodic sweep (run from main.py's lifespan) flips
a department to 'offline' if last_ping_at is older than
HEARTBEAT_TIMEOUT.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from app.db import AsyncSessionLocal
from app.models import Department
from sqlalchemy import update

log = logging.getLogger(__name__)

HEARTBEAT_TIMEOUT = timedelta(seconds=60)
SWEEP_INTERVAL = 20  # seconds


async def heartbeat_sweeper(stop_event: asyncio.Event) -> None:
    """Background task: mark stale departments offline."""
    while not stop_event.is_set():
        try:
            cutoff = datetime.now(timezone.utc) - HEARTBEAT_TIMEOUT
            async with AsyncSessionLocal() as db:
                await db.execute(
                    update(Department)
                    .where(Department.last_ping_at < cutoff)
                    .where(Department.status != "offline")
                    .values(status="offline")
                )
                await db.commit()
        except Exception as e:  # noqa: BLE001
            log.exception("heartbeat sweep failed: %s", e)

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=SWEEP_INTERVAL)
        except asyncio.TimeoutError:
            continue
