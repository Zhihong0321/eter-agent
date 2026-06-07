"""Message handlers - thin adapters that parse, persist, and fan out.

DB writes happen here. The actual WebSocket fan-out is delegated
back to the DepartmentRoom. Wire format is JSON dicts; the
'type' field dispatches to the right handler.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket
from sqlalchemy import select

from app.db import AsyncSessionLocal
from app.models import Approval, Department, Message, Preview, Task
from app.room import DepartmentRoom

log = logging.getLogger(__name__)


# ---------------- user -> server (HoD on phone) ----------------

async def handle_user_chat(
    room: DepartmentRoom, msg: dict[str, Any], _ws: WebSocket
) -> None:
    async with AsyncSessionLocal() as db:
        m = Message(
            session_id=msg["session_id"],
            role="user",
            content=msg["content"],
        )
        db.add(m)
        await db.commit()

    await room.send_to_agents(
        {
            "type": "agent_command",
            "session_id": msg["session_id"],
            "content": msg["content"],
        }
    )


async def handle_user_approval_response(
    room: DepartmentRoom, msg: dict[str, Any]
) -> None:
    async with AsyncSessionLocal() as db:
        a = await db.get(Approval, msg["approval_id"])
        if not a:
            log.warning("approval %s not found", msg["approval_id"])
            return
        a.status = msg["decision"]
        a.response_note = msg.get("note")
        a.resolved_at = datetime.now(timezone.utc)
        await db.commit()

    await room.send_to_agents(
        {
            "type": "approval_result",
            "approval_id": msg["approval_id"],
            "decision": msg["decision"],
            "note": msg.get("note"),
        }
    )


# ---------------- agent -> server (Mac daemon) ----------------

async def handle_agent_chat(room: DepartmentRoom, msg: dict[str, Any]) -> None:
    async with AsyncSessionLocal() as db:
        m = Message(
            session_id=msg["session_id"],
            role=msg.get("role", "agent"),
            content=msg["content"],
        )
        db.add(m)
        await db.commit()

    await room.broadcast_to_users(
        {
            "type": "push_to_user",
            "session_id": msg["session_id"],
            "content": msg["content"],
            "role": msg.get("role", "agent"),
        }
    )


async def handle_agent_state_update(
    room: DepartmentRoom, msg: dict[str, Any]
) -> None:
    tasks = msg.get("tasks", [])
    async with AsyncSessionLocal() as db:
        for item in tasks:
            key = item.get("key")
            if not key:
                continue
            existing = await db.scalar(
                select(Task).where(
                    Task.department_id == room.department_id, Task.key == key
                )
            )
            if existing:
                existing.title = item.get("title", existing.title)
                existing.status = item.get("status", existing.status)
                existing.detail = item.get("detail", existing.detail)
                existing.payload = item.get("payload", existing.payload)
            else:
                db.add(
                    Task(
                        department_id=room.department_id,
                        key=key,
                        title=item.get("title", key),
                        status=item.get("status", "pending"),
                        detail=item.get("detail"),
                        payload=item.get("payload"),
                    )
                )
        await db.commit()

    await room.broadcast_to_users(
        {"type": "state_update", "tasks": tasks}
    )


async def handle_agent_request_approval(
    room: DepartmentRoom, msg: dict[str, Any]
) -> None:
    async with AsyncSessionLocal() as db:
        a = Approval(
            department_id=room.department_id,
            session_id=msg["session_id"],
            plan_id=msg["plan_id"],
            summary=msg["summary"],
            plan=msg["plan"],
            status="pending",
        )
        db.add(a)
        await db.commit()
        await db.refresh(a)
        approval_id = a.id

    await room.broadcast_to_users(
        {
            "type": "approval_request",
            "approval_id": approval_id,
            "plan_id": msg["plan_id"],
            "summary": msg["summary"],
            "plan": msg["plan"],
        }
    )


async def handle_agent_staging_preview(
    room: DepartmentRoom, msg: dict[str, Any]
) -> None:
    async with AsyncSessionLocal() as db:
        db.add(
            Preview(
                department_id=room.department_id,
                url=msg["url"],
                label=msg.get("label", "staging"),
                expires_at=msg.get("expires_at"),
            )
        )
        dept = await db.get(Department, room.department_id)
        if dept:
            dept.last_ping_at = datetime.now(timezone.utc)
        await db.commit()

    await room.broadcast_to_users(
        {
            "type": "staging_preview",
            "url": msg["url"],
            "label": msg.get("label", "staging"),
        }
    )


async def handle_agent_heartbeat(
    room: DepartmentRoom, msg: dict[str, Any]
) -> None:
    async with AsyncSessionLocal() as db:
        dept = await db.get(Department, room.department_id)
        if not dept:
            dept = Department(
                id=room.department_id, name=room.department_id, status="online"
            )
            db.add(dept)
        dept.status = msg.get("status", "online")
        dept.last_ping_at = datetime.now(timezone.utc)
        await db.commit()
